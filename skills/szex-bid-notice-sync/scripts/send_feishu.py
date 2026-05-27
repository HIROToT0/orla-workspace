#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发送飞书通知（每日抓取简报）"""
import json, sys, urllib.request
from datetime import datetime
from pathlib import Path

FEISHU_APP_ID = "cli_a920358585225bd1"
FEISHU_APP_SECRET = "Fteb38eMhHsdA1EhxMmfah86bjGa8Nmj"
FEISHU_USER_ID = "ou_fac5c42357dbdb9c1dd2bf685f731176"
LOG_FILE = Path("/vol1/@apphome/trim.openclaw/data/workspace/szex-bid-notice-sync/logs/cron.log")
RESULT_FILE = Path("/vol1/@apphome/trim.openclaw/data/workspace/szex-bid-notice-sync/logs/.last_result.json")


def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=10)
    body = json.loads(resp.read())
    return body.get("tenant_access_token", "")


def send_feishu_message(token, user_id, content):
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    payload = {
        "receive_id": user_id,
        "msg_type": "text",
        "content": json.dumps({"text": content})
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read()).get("code") == 0


def extract(block, label):
    """从日志块中提取指定标签的值，支持中英文冒号"""
    for line in block.split("\n"):
        if label in line:
            # 支持中文冒号和英文冒号
            if "：" in line:
                parts = line.split("：")
            elif ":" in line:
                parts = line.split(":")
            else:
                continue
            if len(parts) >= 2:
                val = parts[-1].strip().replace(" 条", "").replace(" 条（将发送邮件通知）", "")
                return val
    return "0"


def parse_log():
    """解析最新一次抓取任务的日志"""
    if not LOG_FILE.exists():
        return None

    blocks = [b for b in LOG_FILE.read_text(encoding="utf-8").split("==========") if b.strip()]
    if len(blocks) < 2:
        return None

    # 找到包含数据源信息的任务块（跳过最后的飞书通知块和"任务结束"块）
    task_block = None
    for block in reversed(blocks):
        if "📡" in block and "API返回总数" in block:
            task_block = block
            break

    if not task_block:
        return None

    # 建设工程部分（数据源一）
    jianshe_block = task_block.split("建设工程")[1].split("阳光采购")[0] if "阳光采购" in task_block else task_block
    api_2851 = extract(jianshe_block, "API返回总数")
    filter_2851 = extract(jianshe_block, "关键词过滤后")

    # 阳光采购部分（数据源二）
    if "阳光采购" in task_block:
        yanguang_block = task_block.split("阳光采购")[1].split("✅")[0]
        api_4161 = extract(yanguang_block, "API返回总数")
        filter_4161 = extract(yanguang_block, "关键词过滤后")
    else:
        api_4161 = filter_4161 = "0"

    # 最终新增数（关键词过滤后 = 实际发邮件的记录数）
    # 注意：关键词过滤后已经包含了去重逻辑，所以直接取这个值
    total_filter = int(filter_2851 or 0) + int(filter_4161 or 0)
    new_total = str(total_filter)

    return {
        "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "api_2851": api_2851,
        "api_4161": api_4161,
        "filter_2851": filter_2851,
        "filter_4161": filter_4161,
        "new_total": new_total,
    }


def main():
    result = parse_log()
    if not result:
        print("无法解析日志，跳过飞书通知")
        return

    RESULT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    new_count = int(result.get("new_total", "0") or 0)
    api_2851 = int(result.get("api_2851", "0") or 0)
    api_4161 = int(result.get("api_4161", "0") or 0)
    filter_2851 = int(result.get("filter_2851", "0") or 0)
    filter_4161 = int(result.get("filter_4161", "0") or 0)

    if new_count > 0:
        header = "📬 招标公告抓取完成"
        detail = f"✅ 发现 **{new_count} 条**新增公告，已触发邮件通知"
    else:
        header = "📬 招标公告抓取完成"
        detail = f"ℹ️ 今日无新增公告（{api_2851 + api_4161} 条数据经关键词过滤后均为0条）"

    body = f"""**{header}**

**抓取时间**：{result['fetch_time']}

**数据源汇总**：
• 建设工程：API返回 {api_2851} 条 → 关键词命中 {filter_2851} 条
• 阳光采购：API返回 {api_4161} 条 → 关键词命中 {filter_4161} 条

{detail}

> 关键词：检测、监测、鉴定、排查、巡查"""

    token = get_tenant_access_token()
    if not token:
        print("获取飞书访问令牌失败")
        return

    ok = send_feishu_message(token, FEISHU_USER_ID, body)
    if ok:
        print(f"✅ 飞书通知已发送")
        print(f"   解析结果: {result}")
    else:
        print(f"❌ 飞书通知发送失败")


if __name__ == "__main__":
    main()
