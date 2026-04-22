#!/usr/bin/env python3
"""
深圳交易集团招标公告抓取 + 飞书同步
关键词：检测、检验、监测、检查、巡查、排查、鉴定
公告类型：招标公告
时间：近一月
"""

import json
import sys
import time
import re
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
SESSION_FILE = SKILL_DIR / "config" / "session.json"

# 飞书应用凭证
FEISHU_APP_ID = "cli_a920358585225bd1"
FEISHU_APP_SECRET = "Fteb38eMhHsdA1EhxMmfah86bjGa8Nmj"

# 深圳交易集团 API
API_BASE = "https://www.szexgrp.com"
API_LIST = f"{API_BASE}/cms/api/v1/trade/content/page"
API_DETAIL = f"{API_BASE}/cms/api/v1/trade/content/detail"
MODEL_ID = 1378
CHANNEL_ID = 2851

# 飞书多维表格
BITABLE_APP_TOKEN = "RG7lbqlijaY5WZs78QpcM6NjnZj"
BITABLE_TABLE_ID = "tblkYHpGG8V6IO2h"

# 关键词（检测类）
KEYWORDS = ["检测", "检验", "监测", "检查", "巡查", "排查", "鉴定"]


def get_feishu_token() -> str:
    """获取飞书 tenant_access_token"""
    resp = httpx.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        timeout=10.0,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"飞书 token 获取失败: {data.get('msg')}")
    return data["tenant_access_token"]


def load_config():
    if not CONFIG_FILE.exists():
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        default_config = {
            "bitable_app_token": BITABLE_APP_TOKEN,
            "bitable_table_id": BITABLE_TABLE_ID,
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_session():
    if SESSION_FILE.exists():
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"synced_content_ids": []}


def save_session(session):
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)


def parse_timestamp(date_str: str) -> int | None:
    """将日期字符串转为毫秒时间戳"""
    if not date_str:
        return None
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
        try:
            dt = datetime.strptime(str(date_str).strip(), fmt)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    try:
        ts = int(float(date_str))
        return ts if ts > 1e12 else ts * 1000
    except (ValueError, TypeError):
        pass
    return None


def fetch_list(page: int = 0, size: int = 50) -> tuple:
    """抓取招标公告列表"""
    date_end = datetime.now().strftime("%Y-%m-%d")
    date_begin = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    payload = {
        "modelId": MODEL_ID,
        "channelId": CHANNEL_ID,
        "fields": [{"fieldName": "jygg_gglxmc_rank1", "fieldValue": "招标公告"}],
        "releaseTimeBegin": date_begin,
        "releaseTimeEnd": date_end,
        "page": page,
        "size": size,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    }

    resp = httpx.post(API_LIST, json=payload, headers=headers, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("data", {}).get("content", [])
    total = data.get("data", {}).get("totalElements", 0)
    return items, total


def filter_by_keywords(items: list) -> list:
    """按关键词过滤"""
    return [item for item in items if any(kw in item.get("title", "") for kw in KEYWORDS)]


def fetch_detail(content_id: int) -> dict:
    """抓取公告详情，解析关键字段"""
    try:
        resp = httpx.get(
            API_DETAIL,
            params={"contentId": content_id},
            headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        txt = data.get("data", {}).get("txt", "")
    except Exception as e:
        return {"error": str(e)}

    if not txt:
        return {}

    # 转为纯文本以便正则匹配
    text = re.sub(r'<[^>]+>', ' ', txt)
    text = re.sub(r'\s+', ' ', text).strip()

    detail = {}

    # 投标文件递交截止时间
    m = re.search(r'投标文件递交截止时间\s+([^\s]{10,19})', text)
    if m:
        raw = m.group(1).strip()
        detail["noticeEndTime"] = raw

    # 发包工程估价
    m = re.search(r'本次发包工程估价\s+([\d.]+)\s*万元', text)
    if m:
        try:
            detail["budget"] = float(m.group(1))
        except ValueError:
            pass

    # 招标方式
    if re.search(r'邀请招标', text):
        detail["purchaseMethod"] = "邀请招标"
    elif re.search(r'公开招标', text):
        detail["purchaseMethod"] = "公开招标"

    # 资格审查方式
    if re.search(r'资格后审', text):
        detail["qualifyMethod"] = "资格后审"
    elif re.search(r'资格预审', text):
        detail["qualifyMethod"] = "资格预审"

    # 递交方式
    if re.search(r'线上递交', text):
        detail["submitMethod"] = "线上递交"
    elif re.search(r'线下递交', text):
        detail["submitMethod"] = "线下递交"

    # 招标概况（摘要前500字）
    m = re.search(r'本次招标内容[:：]?\s*(.{10,500}?)(?:投标人|投标文件|招标人|代理|资质|$)', text, re.DOTALL)
    if m:
        detail["summary"] = m.group(1).strip()[:500]
    else:
        # 备选：找 "本次招标" 后的文字
        m = re.search(r'本次招标[^\n]{20,300}', text)
        if m:
            detail["summary"] = m.group(0).strip()[:300]

    return detail


def get_existing_ids(token: str) -> set:
    """获取表格中已有的 contentId 列表"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records?page_size=100"
    existing_ids = set()

    while url:
        resp = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15.0)
        if resp.status_code != 200:
            break
        data = resp.json()
        for record in data.get("data", {}).get("items", []):
            link = record.get("fields", {}).get("公告链接", {})
            if isinstance(link, dict):
                m = re.search(r"contentId=(\d+)", link.get("link", ""))
                if m:
                    existing_ids.add(m.group(1))
        page_info = data.get("data", {})
        url = None
        if page_info.get("has_more") and page_info.get("page_token"):
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records?page_token={page_info['page_token']}"

    return existing_ids


def sync_to_bitabel(token: str, items: list, existing_ids: set, dry_run: bool = False) -> dict:
    """同步到飞书多维表格"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    results = {"success": 0, "skipped": 0, "failed": 0}
    now_ms = int(datetime.now().timestamp() * 1000)

    for item in items:
        content_id = str(item.get("id", ""))

        if content_id in existing_ids and not dry_run:
            results["skipped"] += 1
            continue

        title = item.get("title", "")
        if not any(kw in title for kw in KEYWORDS):
            continue

        if not dry_run:
            detail = fetch_detail(int(content_id))
        else:
            detail = {}

        notice_end_time = parse_timestamp(detail.get("noticeEndTime", ""))
        fields = {
            "公告名称": title,
            "公告链接": {
                "text": "查看公告",
                "link": f"{API_BASE}/jyfw/details.html?contentId={content_id}&channelId={CHANNEL_ID}&crumb=jsgc",
            },
            "公告类型": "招标公告",
            "子类型": "招标公告",
            "工程类型": item.get("projectType") or "其他",
            "发布时间": parse_timestamp(item.get("publishTime", "")),
            "投标截止时间": notice_end_time,
            "招标估算": detail.get("budget"),
            "招标方式": detail.get("purchaseMethod", "公开招标"),
            "资格审查方式": detail.get("qualifyMethod", ""),
            "递交方式": detail.get("submitMethod", ""),
            "招标概况": detail.get("summary", ""),
            "抓取时间": now_ms,
        }

        if dry_run:
            print(f"   [DRY] {title[:50]}")
            results["success"] += 1
            continue

        try:
            resp = httpx.post(url, json={"fields": fields}, headers=headers, timeout=15.0)
            if resp.status_code in (200, 201):
                results["success"] += 1
                print(f"   ✅ {title[:40]}")
            else:
                results["failed"] += 1
                print(f"   ❌ {resp.text[:80]}")
        except Exception as e:
            results["failed"] += 1
            print(f"   ❌ {e}")

        time.sleep(0.5)  # 避免触发频率限制

    return results


def backfill_details(token: str, dry_run: bool = False) -> dict:
    """回填已有记录的详情（投标截止时间/招标估算/招标概况等）"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records?page_size=100"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    results = {"updated": 0, "skipped": 0, "failed": 0}

    page_token = None

    while True:
        resp_url = url + (f"&page_token={page_token}" if page_token else "")
        resp = httpx.get(resp_url, headers=headers, timeout=15.0)
        if resp.status_code != 200:
            break

        data = resp.json()
        items = data.get("data", {}).get("items", [])
        has_more = data.get("data", {}).get("has_more", False)
        page_token = data.get("data", {}).get("page_token", "") or None

        for record in items:
            fields = record.get("fields", {})
            record_id = record.get("record_id", "")

            # 检查是否需要回填
            need_update = False
            new_fields = {}

            # 投标截止时间、招标估算、招标方式、资格审查方式、递交方式、招标概况
            # 只要有一个为空就尝试回填
            empty_checks = ["投标截止时间", "招标估算", "招标方式", "资格审查方式", "递交方式", "招标概况"]
            has_empty = any(not fields.get(f) for f in empty_checks)

            if not has_empty:
                results["skipped"] += 1
                continue

            link = fields.get("公告链接", {})
            if not isinstance(link, dict):
                results["skipped"] += 1
                continue

            m = re.search(r"contentId=(\d+)", link.get("link", ""))
            if not m:
                results["skipped"] += 1
                continue

            content_id = m.group(1)
            title = fields.get("公告名称", "")[:40]

            if dry_run:
                print(f"   [DRY] 回填 {title}")
                results["updated"] += 1
                continue

            detail = fetch_detail(int(content_id))

            if not detail or "error" in detail:
                results["failed"] += 1
                print(f"   ⚠️  {title}: 获取详情失败")
                continue

            # 准备更新字段
            if not fields.get("投标截止时间") and detail.get("noticeEndTime"):
                new_fields["投标截止时间"] = parse_timestamp(detail["noticeEndTime"])
                need_update = True

            if not fields.get("招标估算") and detail.get("budget"):
                new_fields["招标估算"] = detail["budget"]
                need_update = True

            if not fields.get("招标方式") and detail.get("purchaseMethod"):
                new_fields["招标方式"] = detail["purchaseMethod"]
                need_update = True

            if not fields.get("资格审查方式") and detail.get("qualifyMethod"):
                new_fields["资格审查方式"] = detail["qualifyMethod"]
                need_update = True

            if not fields.get("递交方式") and detail.get("submitMethod"):
                new_fields["递交方式"] = detail["submitMethod"]
                need_update = True

            if not fields.get("招标概况") and detail.get("summary"):
                new_fields["招标概况"] = detail["summary"]
                need_update = True

            if need_update:
                try:
                    update_url = f"{url.replace('?page_size=100','')}/{record_id}"
                    upd_resp = httpx.put(
                        update_url,
                        json={"fields": new_fields},
                        headers=headers,
                        timeout=15.0,
                    )
                    if upd_resp.status_code in (200, 201):
                        results["updated"] += 1
                        print(f"   ✅ 回填 {title}")
                    else:
                        results["failed"] += 1
                        print(f"   ❌ 回填 {title}: {upd_resp.text[:60]}")
                except Exception as e:
                    results["failed"] += 1
                    print(f"   ❌ 回填 {title}: {e}")
            else:
                results["skipped"] += 1

            time.sleep(0.5)

        if not has_more or not page_token:
            break

    return results


def main():
    parser = argparse.ArgumentParser(description="深圳交易集团检测类招标公告抓取")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backfill", action="store_true", help="回填已有记录的详情字段")
    args = parser.parse_args()

    print(f"🔍 深圳交易集团招标公告抓取")
    if args.backfill:
        print("   [模式] 回填已有记录的详情字段")
    else:
        print(f"   关键词: {KEYWORDS}")
        print(f"   日期范围: 近{args.days}天")

    config = load_config()
    session = load_session()
    synced_ids = set(session.get("synced_content_ids", []))

    print("   获取飞书 token...")
    token = get_feishu_token()

    if args.backfill:
        print("   开始回填...")
        results = backfill_details(token, dry_run=args.dry_run)
        print(f"\n✅ 回填完成: 更新 {results['updated']}, 跳过 {results['skipped']}, 失败 {results['failed']}")
        return

    # 检查已有记录
    print("   检查已有记录...")
    existing_ids = get_existing_ids(token) if not args.dry_run else set()
    print(f"   已有 {len(existing_ids)} 条记录")

    # 抓取
    all_matched = []
    page = 0

    while True:
        items, total = fetch_list(page=page)
        print(f"   第 {page+1} 页: {len(items)} 条 (总计 {total})")

        filtered = filter_by_keywords(items)
        for item in filtered:
            cid = str(item.get("id", ""))
            if cid not in synced_ids and cid not in existing_ids:
                all_matched.append(item)

        if len(items) < 50 or (page + 1) * 50 >= total:
            break
        page += 1
        time.sleep(0.5)

    print(f"\n📦 关键词匹配: {len(all_matched)} 条新增")

    if not all_matched:
        print("没有新的检测类公告 ✅")
        return

    results = sync_to_bitabel(token, all_matched, existing_ids, dry_run=args.dry_run)
    print(f"\n✅ 完成: 成功 {results['success']}, 跳过 {results['skipped']}, 失败 {results['failed']}")

    for item in all_matched:
        cid = str(item.get("id", ""))
        if cid:
            synced_ids.add(cid)

    session["synced_content_ids"] = list(synced_ids)[-2000:]
    save_session(session)


if __name__ == "__main__":
    main()