#!/usr/bin/env python3
"""
深圳交易集团招标公告抓取 + 飞书同步
用法: python3 fetch_and_sync.py [--days 7] [--types 其他,施工] [--dry-run]
"""

import json
import sys
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

try:
    import httpx
except ImportError:
    print("❌ 请安装 httpx: pip install httpx")
    sys.exit(1)

# ========== 配置 ==========
SKILL_DIR = Path(__file__).parent.parent
CONFIG_FILE = SKILL_DIR / "config" / "config.json"
EMAIL_CONFIG_FILE = SKILL_DIR / "config" / "email.json"
SESSION_FILE = SKILL_DIR / "config" / "session.json"
REFERENCES_DIR = SKILL_DIR / "references"

# 深圳交易集团 API
API_BASE = "https://www.szexgrp.com/cms/api/v1/trade/content"
MODEL_ID = 1378
CHANNEL_ID = 2851

# 工程类型映射
PROJECT_TYPES = {
    "施工": "施工",
    "监理": "监理",
    "勘察": "勘察",
    "设计": "设计",
    "可研": "可研",
    "货物": "货物",
    "物业": "物业",
    "其他": "其他",
}


def load_config():
    if not CONFIG_FILE.exists():
        print(f"❌ 配置文件不存在: {CONFIG_FILE}")
        print("   复制 config/config.json.example 到 config/config.json")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_email_config():
    if not EMAIL_CONFIG_FILE.exists():
        return None
    with open(EMAIL_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_session():
    if SESSION_FILE.exists():
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"synced_ids": []}


def save_session(session):
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)


def fetch_announcements(date_begin: str, date_end: str, types: list, page: int = 0, size: int = 50):
    """抓取招标公告列表"""
    url = f"{API_BASE}/page"

    filters = [{"fieldName": "jygg_gglxmc_rank1", "fieldValue": "招标公告"}]
    if types:
        type_filter = ",".join(types)
        filters.append({"fieldName": "jygg_gclx", "fieldValue": type_filter})

    payload = {
        "modelId": MODEL_ID,
        "channelId": CHANNEL_ID,
        "fields": filters,
        "releaseTimeBegin": date_begin,
        "releaseTimeEnd": date_end,
        "page": page,
        "size": size,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
    response.raise_for_status()
    return response.json()


def parse_list_response(data: dict) -> tuple:
    """解析列表响应，返回 (公告列表, 总数)"""
    if "data" in data and "content" in data["data"]:
        items = data["data"]["content"]
        total = data["data"].get("totalElements", len(items))
        return items, total
    return [], 0


def build_detail_url(item: dict) -> str:
    """从字段提取详情页URL"""
    # details.html 格式拼接
    doc_id = item.get("id") or item.get("docId") or item.get("docid", "")
    return f"https://www.szexgrp.com/cms/api/v1/trade/content/{doc_id}/detail"


def fetch_detail(detail_url: str) -> dict:
    """抓取单条公告详情"""
    try:
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        response = httpx.get(detail_url, headers=headers, timeout=15.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"   ⚠️ 详情获取失败: {e}")
        return {}


def extract_fields(item: dict, detail: dict = None) -> dict:
    """提取关键字段"""
    fields = item.copy() if item else {}

    # 通用字段
    fields["title"] = item.get("title", "")
    fields["doc_id"] = item.get("id", "") or item.get("docId", "")
    fields["publish_time"] = item.get("releaseTime", "") or item.get("publishTime", "")
    fields["project_type"] = item.get("jygg_gclx", "")
    fields["category"] = item.get("jygg_gglxmc_rank1", "")

    if detail:
        # 详情页字段
        fields["bid_deadline"] = detail.get("jygg_tbsj", "") or detail.get("bidDeadline", "")
        fields["budget"] = detail.get("jygg_fbgcgs", "") or detail.get("budget", "")
        fields["tender_method"] = detail.get("jygg_zbfs", "") or detail.get("tenderMethod", "")
        fields["qualify_method"] = detail.get("jygg_zgfs", "") or detail.get("qualifyMethod", "")
        fields["submit_method"] = detail.get("jygg_djfs", "") or detail.get("submitMethod", "")
        fields["summary"] = detail.get("jygg_ggnr", "") or detail.get("summary", "")

    return fields


def bitable_timestamp(date_str: str) -> int:
    """将日期字符串转为毫秒时间戳（飞书日期字段格式）"""
    if not date_str:
        return None
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"]:
        try:
            dt = datetime.strptime(str(date_str), fmt)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    # 尝试解析时间戳
    try:
        ts = int(float(date_str))
        if ts > 1e12:  # 毫秒
            return ts
        elif ts > 1e9:  # 秒转毫秒
            return ts * 1000
    except (ValueError, TypeError):
        pass
    return None


def sync_to_bitabel(config: dict, records: list, dry_run: bool = False) -> dict:
    """同步记录到飞书多维表格"""
    app_token = config.get("app_token")
    table_id = config.get("table_id")
    if not app_token or not table_id:
        print("❌ config.json 缺少 app_token 或 table_id")
        sys.exit(1)

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"

    headers = {
        "Authorization": f"Bearer {config.get('feishu_token', '')}",
        "Content-Type": "application/json",
    }

    results = {"success": 0, "failed": 0, "skipped": 0}

    for record in records:
        if dry_run:
            print(f"   [DRY] {record.get('title', 'N/A')[:50]}")
            results["success"] += 1
            continue

        # 构建飞书记录格式
        fields = {
            "公告名称": record.get("title", ""),
            "公告链接": {"text": record.get("title", ""), "link": record.get("detail_url", "")},
            "公告类型": record.get("category", ""),
            "工程类型": record.get("project_type", ""),
            "发布时间": bitable_timestamp(record.get("publish_time", "")),
            "投标截止时间": bitable_timestamp(record.get("bid_deadline", "")),
            "招标估算": float(record.get("budget", 0)) if record.get("budget") else None,
            "招标方式": record.get("tender_method", ""),
            "资格审查方式": record.get("qualify_method", ""),
            "递交方式": record.get("submit_method", ""),
            "招标概况": record.get("summary", ""),
            "抓取时间": int(datetime.now().timestamp() * 1000),
            "状态": "待跟进",
        }

        payload = {"fields": fields}

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=15.0)
            if response.status_code == 200:
                results["success"] += 1
                print(f"   ✅ {record.get('title', '')[:40]}")
            else:
                results["failed"] += 1
                print(f"   ❌ {response.text[:80]}")
        except Exception as e:
            results["failed"] += 1
            print(f"   ❌ {e}")

        time.sleep(0.3)  # 避免限流

    return results


def send_email_notification(email_config: dict, new_records: list, total: int):
    """发送邮件通知"""
    if not email_config or not new_records:
        return

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
    except ImportError:
        print("⚠️ email.mime 未安装，跳过邮件通知")
        return

    smtp_host = email_config.get("smtp_host")
    smtp_port = email_config.get("smtp_port", 465)
    smtp_user = email_config.get("smtp_user")
    smtp_pass = email_config.get("smtp_pass")
    to_emails = email_config.get("to", [])

    if not all([smtp_host, smtp_user, smtp_pass, to_emails]):
        print("⚠️ 邮件配置不完整，跳过")
        return

    # 构建邮件内容
    body = f"<h2>深圳交易集团招标公告 - 新增 {len(new_records)} 条</h2>"
    body += f"<p>抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>"
    body += "<hr>"
    for r in new_records[:20]:  # 最多20条
        body += f"<li><a href='{r.get('detail_url','')}'>{r.get('title','N/A')}</a> "
        body += f"| 类型:{r.get('project_type','')} "
        body += f"| 截止:{r.get('bid_deadline','N/A')}</li>"
    if len(new_records) > 20:
        body += f"<p>...还有 {len(new_records)-20} 条</p>"

    msg = MIMEMultipart("html")
    msg["Subject"] = f"【招标公告】新增 {len(new_records)} 条 ({datetime.now().strftime('%m/%d')})"
    msg["From"] = smtp_user
    msg["To"] = ",".join(to_emails)
    msg.attach(MIMEText(body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_emails, msg.as_string())
        print("✅ 邮件发送成功")
    except Exception as e:
        print(f"⚠️ 邮件发送失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="深圳交易集团招标公告抓取")
    parser.add_argument("--days", type=int, default=7, help="抓取最近N天的公告 (默认7)")
    parser.add_argument("--types", type=str, default="其他", help="工程类型，逗号分隔 (默认:其他)")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不写入飞书")
    parser.add_argument("--all-types", action="store_true", help="抓取所有工程类型")
    args = parser.parse_args()

    config = load_config()

    # 时间范围
    date_end = datetime.now().strftime("%Y-%m-%d")
    date_begin = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    types = None if args.all_types else [t.strip() for t in args.types.split(",")]

    print(f"📡 开始抓取: {date_begin} ~ {date_end}")
    if types:
        print(f"   工程类型: {types}")
    else:
        print(f"   工程类型: 全部")

    # 加载已同步记录
    session = load_session()
    synced_ids = set(session.get("synced_ids", []))

    all_new = []
    page = 0

    while True:
        try:
            data = fetch_announcements(date_begin, date_end, types, page=page)
            items, total = parse_list_response(data)
        except Exception as e:
            print(f"❌ API 请求失败: {e}")
            sys.exit(1)

        print(f"   第 {page+1} 页: 获取 {len(items)} 条 (总计 {total})")

        for item in items:
            doc_id = str(item.get("id", "") or item.get("docId", ""))
            if doc_id in synced_ids:
                continue

            detail_url = build_detail_url(item)
            detail = fetch_detail(detail_url)
            fields = extract_fields(item, detail)
            fields["detail_url"] = detail_url
            fields["doc_id"] = doc_id

            all_new.append(fields)
            synced_ids.add(doc_id)

        if len(items) < 50 or (page + 1) * 50 >= total:
            break
        page += 1
        time.sleep(0.5)

    print(f"\n📦 本次新增: {len(all_new)} 条")

    if all_new:
        results = sync_to_bitabel(config, all_new, dry_run=args.dry_run)
        print(f"\n✅ 同步完成: 成功 {results['success']}, 失败 {results['failed']}, 跳过 {results['skipped']}")

        # 保存同步记录
        session["synced_ids"] = list(synced_ids)[-5000:]  # 最多保留5000条
        save_session(session)

        # 邮件通知
        email_config = load_email_config()
        if email_config:
            send_email_notification(email_config, all_new, len(all_new))
    else:
        print("没有新公告需要同步")

    print(f"\n总计已同步: {len(synced_ids)} 条")


if __name__ == "__main__":
    main()