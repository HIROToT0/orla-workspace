#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送招标公告更新邮件
依赖: Python 3.8+, smtplib (标准库)
"""
import json, smtplib, ssl, sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

EMAIL_CFG = Path(__file__).parent.parent / "config" / "email.json"
LAST_NEW = Path(__file__).parent.parent / "config" / ".last_keyword_new.txt"
TABLE_URL = "https://ccnlg9zq6b6x.feishu.cn/base/RG7lbqlijaY5WZs78QpcM6NjnZj?table=tblkYHpGG8V6IO2h&view=vewVmCznTB"
FETCH_TIME = Path(__file__).parent.parent / "config" / ".fetch_time.txt"


def load_cfg():
    with open(EMAIL_CFG) as f:
        return json.load(f)


def load_records():
    """加载含关键词的新增记录（JSON格式，含标题、类型、链接等）"""
    if not LAST_NEW.exists():
        return []
    try:
        content = LAST_NEW.read_text(encoding="utf-8").strip()
        # 文件存在但内容为空或为[]，都视为无数据
        if not content or content == "[]":
            return []
        return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return []


def build_html_table(records, fetch_time=""):
    """构建HTML表格"""
    if not records:
        return ""

    rows = []
    for idx, rec in enumerate(records, 1):
        title = rec.get("title", "")
        notice_type = rec.get("notice_type", "")
        url = rec.get("url", "")
        publish_time = rec.get("publish_time", "")

        # 处理发布时间格式
        if publish_time and len(str(publish_time)) >= 10:
            try:
                dt = datetime.strptime(str(publish_time)[:10], "%Y-%m-%d")
                publish_time = dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        rows.append(f"""
        <tr style="background-color: {'#f5f5f5' if idx % 2 == 0 else '#ffffff'};">
            <td style="padding:10px; border:1px solid #ddd; text-align:center;">{idx}</td>
            <td style="padding:10px; border:1px solid #ddd;">
                <a href="{url}" style="color:#1a73e8; text-decoration:none; word-break:break-all;">{title}</a>
            </td>
            <td style="padding:10px; border:1px solid #ddd; text-align:center; white-space:nowrap;">{notice_type}</td>
            <td style="padding:10px; border:1px solid #ddd; text-align:center; white-space:nowrap;">{publish_time}</td>
        </tr>
        """)

    table_html = f"""
    <div style="margin:20px 0;">
        <p style="font-size:14px; color:#666;">抓取时间：{fetch_time} &nbsp;|&nbsp; 共 <strong>{len(records)}</strong> 条新增公告</p>
        <table style="width:100%; border-collapse:collapse; font-size:14px; font-family:Microsoft YaHei, Arial, sans-serif;">
            <thead>
                <tr style="background-color:#2c5aa0; color:#ffffff;">
                    <th style="padding:12px 10px; border:1px solid #ddd; text-align:center; width:40px;">序号</th>
                    <th style="padding:12px 10px; border:1px solid #ddd; text-align:left;">公告名称</th>
                    <th style="padding:12px 10px; border:1px solid #ddd; text-align:center; width:120px;">公告类型</th>
                    <th style="padding:12px 10px; border:1px solid #ddd; text-align:center; width:100px;">发布时间</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
    </div>
    """
    return table_html


def build_plain_table(records):
    """构建纯文本表格（作为plain版本fallback）"""
    if not records:
        return ""
    lines = ["📋 本次新增招标公告：", ""]
    header = f"{'序号':<6} {'公告名称':<60} {'类型':<15} {'发布时间':<12}"
    lines.append(header)
    lines.append("-" * 100)
    for idx, rec in enumerate(records, 1):
        title = rec.get("title", "")[:58]
        notice_type = rec.get("notice_type", "")[:13]
        publish_time = rec.get("publish_time", "")[:10]
        if len(str(publish_time)) >= 10:
            try:
                dt = datetime.strptime(str(publish_time)[:10], "%Y-%m-%d")
                publish_time = dt.strftime("%Y-%m-%d")
            except Exception:
                pass
        lines.append(f"{idx:<6} {title:<60} {notice_type:<15} {publish_time:<12}")
    return "\n".join(lines)


def send_email(records):
    cfg = load_cfg()
    if not records:
        print("无新增记录，跳过发送邮件")
        return

    # 获取抓取时间
    fetch_time = ""
    if FETCH_TIME.exists():
        fetch_time = FETCH_TIME.read_text().strip()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{cfg['subject_prefix']}新增 {len(records)} 条公告"
    msg["From"] = f"{cfg['from_name']} <{cfg['from_addr']}>"
    msg["To"] = ", ".join(cfg["to_addrs"])

    # Plain文本版本
    plain_body = build_plain_table(records)
    plain_body += f"\n\n🔗 表格链接：{TABLE_URL}"
    text_part = MIMEText(plain_body, "plain", "utf-8")

    # HTML版本
    table_html = build_html_table(records, fetch_time)
    html_body = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Microsoft YaHei, Arial, sans-serif; color: #333; }}
        </style>
    </head>
    <body>
        <h2 style="color:#2c5aa0; margin-bottom:5px;">📋 深圳交易集团招标公告更新</h2>
        <p style="color:#666; font-size:13px;">
            以下为本次新增的招标公告，请及时查看。
        </p>
        {table_html}
        <p style="margin-top:20px;">
            <a href="{TABLE_URL}" style="display:inline-block; padding:10px 20px; background-color:#2c5aa0; color:#ffffff; text-decoration:none; border-radius:4px; font-size:14px;">
                🔗 点击查看完整表格
            </a>
        </p>
        <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
        <p style="color:#999; font-size:12px;">本邮件由系统自动发送，请勿直接回复。</p>
    </body>
    </html>
    """
    html_part = MIMEText(html_body, "html", "utf-8")

    msg.attach(text_part)
    msg.attach(html_part)

    if cfg.get("use_ssl", True):
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(cfg["smtp_host"], cfg["smtp_port"], context=ctx) as server:
            server.login(cfg["from_addr"], cfg.get("password", ""))
            server.sendmail(cfg["from_addr"], cfg["to_addrs"], msg.as_string())
    else:
        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
            server.starttls()
            server.login(cfg["from_addr"], cfg.get("password", ""))
            server.sendmail(cfg["from_addr"], cfg["to_addrs"], msg.as_string())

    print(f"✅ 邮件已发送至 {', '.join(cfg['to_addrs'])}，共 {len(records)} 条记录")


if __name__ == "__main__":
    records = load_records()
    send_email(records)