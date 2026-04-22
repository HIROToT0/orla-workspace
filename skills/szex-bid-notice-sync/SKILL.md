---
name: szex-bid-notice-sync
description: 深圳交易集团招标公告抓取 + 飞书多维表格同步。关键词：检测/检验/监测/检查/巡查/排查/鉴定，工程类型全部，公告类型招标公告。触发词：「招标公告」「深圳交易集团」「抓取招标」「szex」「bid notice」
---

# 深圳交易集团招标公告同步

## 功能

- ✅ 按关键词（检测/检验/监测/检查/巡查/排查/鉴定）筛选招标公告
- ✅ 近3天增量抓取（可配置）
- ✅ 自动去重（基于 contentId）
- ✅ 写入飞书多维表格（公告名称、链接、类型、工程类型、发布时间、投标截止时间、招标估算、招标方式、资格审查方式、递交方式、招标概况、抓取时间）
- ✅ 回填已有记录的详情字段（`--backfill`）
- ✅ 每日定时任务（crontab，每天 07:00）

## 使用方式

### 1. 抓取新公告

```bash
cd ~/.openclaw/workspace/skills/szex-bid-notice-sync/scripts
python3 fetch_and_sync.py                    # 默认抓取近30天关键词匹配
python3 fetch_and_sync.py --days 3            # 抓取近3天（每日定时推荐）
python3 fetch_and_sync.py --dry-run           # 测试模式，不写入飞书
```

### 2. 回填历史记录的详情字段

```bash
python3 fetch_and_sync.py --backfill          # 回填已有记录的投标截止时间/招标估算/招标概况等
python3 fetch_and_sync.py --backfill --dry-run # 测试模式
```

### 3. 定时任务

```bash
# 每天07:00执行，抓取近3天数据
0 7 * * * cd /path/to/scripts && python3 fetch_and_sync.py --days 3 >> /tmp/szex-bid-notice-sync.log 2>&1
```

## 配置

`config/config.json`（自动生成，勿提交）:
```json
{
  "bitable_app_token": "RG7lbqlijaY5WZs78QpcM6NjnZj",
  "bitable_table_id": "tblkYHpGG8V6IO2h"
}
```

飞书 token 从 OpenClaw 配置自动获取，无需手动填写。

## 文件结构

```
szex-bid-notice-sync/
├── SKILL.md                    # 本文件
├── README.md                   # 详细说明
├── .gitignore                  # 忽略 config.json / session.json / 日志
├── scripts/
│   └── fetch_and_sync.py       # 主脚本
├── config/
│   ├── config.json.example     # 配置模板
│   ├── config.json             # 运行时配置（不提交）
│   ├── session.json            # 已同步 ID 记录（不提交）
│   └── email.json.example      # 邮件通知配置模板
└── references/
    └── api-fields.md            # 深圳交易集团 API 字段说明
```

## API 信息

- 列表 API: `POST https://www.szexgrp.com/cms/api/v1/trade/content/page`
- 详情 API: `GET https://www.szexgrp.com/cms/api/v1/trade/content/detail?contentId=X`
- modelId: 1378, channelId: 2851（建设工程）
- 关键词过滤在本地进行（API 不支持关键词查询）
- 回填时跳过变更记录（截标信息/招标文件变更等无详情）