---
name: szex-bid-notice-sync
description: "深圳交易集团招标公告抓取 + 飞书多维表格同步 + 邮件通知。定期从深圳交易集团官网抓取招标公告（含建设工程/阳光采购双数据源），过滤关键词后写入飞书多维表格，并发送邮件/飞书通知。"
version: "1.0.0"
changelog: "初始版本：支持双数据源（建设工程 channelId=2851，阳光采购 channelId=4161），关键词过滤，写入飞书多维表格，邮件+飞书通知。"
metadata: {"clawdbot":{"emoji":"🏛️","requires":{"bins":["python3"]}}}
---

# 深圳交易集团招标公告抓取

从深圳交易集团官网抓取招标公告，自动同步到飞书多维表格并发送通知邮件。

## 功能特性

- **双数据源**：建设工程（channelId=2851）+ 阳光采购（channelId=4161）
- **关键词过滤**：检测、监测、鉴定、排查、巡查
- **自动同步**：写入飞书多维表格（自动创建字段）
- **多端通知**：邮件 + 飞书机器人消息
- **去重**：基于公告名称去重，避免重复写入

## 目录结构

```
szex-bid-notice-sync/
├── SKILL.md                  # 本文件
├── README.md                 # 项目说明
├── config/
│   ├── config.json           # 主配置（飞书 app_token / table_id / 关键词）
│   └── email.json            # 邮件配置（SMTP）
├── scripts/
│   ├── fetch_and_sync.py     # 主脚本：抓取 + 写入飞书
│   ├── send_email.py        # 邮件通知脚本
│   ├── send_feishu.py       # 飞书通知脚本
│   └── run_daily.sh         # 每日定时运行脚本
└── logs/
    ├── cron.log              # 每日抓取日志
    └── .last_result.json    # 最近一次抓取结果摘要
```

## 脚本说明

### fetch_and_sync.py — 抓取 + 同步

```bash
python3 scripts/fetch_and_sync.py
```

**输入**：从 `~/.openclaw/openclaw.json` 读取飞书应用凭证  
**配置**：`config/config.json`

```json
{
  "app_token": "飞书多维表格 AppToken",
  "table_id": "数据表 ID",
  "days": 3,
  "keywords": ["检测", "监测", "鉴定", "排查", "巡查"],
  "project_types": []
}
```

**输出**：
- 打印抓取进度和结果
- 匹配关键词的新增记录写入 `config/.last_keyword_new.txt`（供邮件脚本使用）
- `config/.fetch_time.txt` 记录抓取时间

**字段映射**（写入飞书多维表格）：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 公告名称 | 文本 | 公告标题 |
| 公告链接 | URL | 公告详情页 |
| 公告类型 | 单选 | 如"招标公告" |
| 子类型 | 单选 | 子类型名称 |
| 工程类型 | 单选 | 项目类型 |
| 发布时间 | 日期 | 发布时间 |
| 投标截止时间 | 日期 | 截止时间 |
| 招标概况 | 文本 | 招标内容描述 |
| 抓取时间 | 日期 | 抓取时间 |
| 状态 | 单选 | 状态（空） |
| 招标估算 | 数字 | 工程估价（万元） |
| 招标方式 | 单选 | 公开招标/邀请招标 |
| 资格审查方式 | 单选 | 资格后审/资格预审 |
| 递交方式 | 单选 | 线上/线下递交 |

### send_email.py — 发送邮件通知

```bash
python3 scripts/send_email.py
```

**输入**：`config/.last_keyword_new.txt`（fetch_and_sync.py 写入）  
**配置**：`config/email.json`

```json
{
  "smtp_host": "smtp.example.com",
  "smtp_port": 465,
  "use_ssl": true,
  "from_addr": "sender@example.com",
  "from_name": "招标公告机器人",
  "password": "smtp_password",
  "to_addrs": ["recipient@example.com"],
  "subject_prefix": "【招标公告】"
}
```

**输出**：发送 HTML 邮件，含表格和链接。

### send_feishu.py — 发送飞书通知

```bash
python3 scripts/send_feishu.py
```

**输入**：`logs/cron.log`（从日志解析抓取结果）  
**凭证**：硬编码在脚本中的飞书应用 `cli_a920358585225bd1`  
**输出**：发送飞书消息卡片到用户 `ou_fac5c42357dbdb9c1dd2bf685f731176`

### run_daily.sh — 每日定时任务

```bash
bash scripts/run_daily.sh
```

依次执行：fetch_and_sync.py → send_feishu.py → send_email.py

## API 信息

### 深圳交易集团

- 列表 API：`POST https://www.szexgrp.com/cms/api/v1/trade/content/page`
- 详情 API：`GET https://www.szexgrp.com/cms/api/v1/trade/content/detail`

### 飞书

- 认证：`POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal`
- 多维表格：`https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records`
- 消息：`POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id`