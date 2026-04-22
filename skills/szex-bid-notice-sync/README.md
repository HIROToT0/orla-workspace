# szex-bid-notice-sync

深圳交易集团招标公告抓取 + 飞书多维表格同步

## 背景

每天监控深圳交易集团官网（https://www.szexgrp.com）招标公告，筛选检测类项目（检测/检验/监测/检查/巡查/排查/鉴定），同步到飞书多维表格。

## 核心流程

```
深圳交易集团 API
        ↓
  Python 脚本（fetch_and_sync.py）
        ↓
  飞书多维表格（深圳交易集团招标公告信息）
        ↓（可选）
    邮件通知
```

## 功能清单

- ✅ 按关键词筛选（检测/检验/监测/检查/巡查/排查/鉴定）
- ✅ 公告类型：招标公告（过滤掉变更/答疑/补遗等）
- ✅ 工程类型：全部（不筛选）
- ✅ 近 N 天数据抓取（默认3天）
- ✅ 自动增量去重（基于 contentId）
- ✅ 详情字段回填（投标截止时间/招标估算/招标方式/资格审查方式/递交方式/招标概况）
- ✅ 飞书多维表格写入（14个字段）
- ✅ 每日定时任务（crontab 07:00）

## 快速开始

### 1. 安装依赖

```bash
pip install httpx
```

### 2. 配置飞书多维表格

已有配置：
- app_token: `RG7lbqlijaY5WZs78QpcM6NjnZj`
- table_id: `tblkYHpGG8V6IO2h`
- 表格：深圳交易集团招标公告信息

如需更换表格，在 `config/config.json` 中修改。

### 3. 运行

```bash
# 首次运行抓取全量（近30天）
python3 scripts/fetch_and_sync.py

# 每日增量（近3天）
python3 scripts/fetch_and_sync.py --days 3

# 回填已有记录的详情字段
python3 scripts/fetch_and_sync.py --backfill

# 测试模式
python3 scripts/fetch_and_sync.py --dry-run
```

### 4. 定时任务

```bash
# 编辑 crontab
crontab -e

# 添加行：
0 7 * * * cd ~/.openclaw/workspace/skills/szex-bid-notice-sync/scripts && python3 fetch_and_sync.py --days 3 >> /tmp/szex-bid-notice-sync.log 2>&1
```

## 飞书多维表格字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 公告名称 | 文本 | 主字段 |
| 公告链接 | 链接 | 指向 szexgrp.com 详情页 |
| 公告类型 | 单选 | 招标公告 / 答疑、补遗 / 截标信息 |
| 子类型 | 单选 | 同上 |
| 工程类型 | 单选 | 施工 / 监理 / 勘察 / 设计 / 其他 等 |
| 发布时间 | 日期 | |
| 投标截止时间 | 日期 | 从详情 API 提取 |
| 招标概况 | 文本 | 从详情 API 提取（前500字） |
| 抓取时间 | 日期 | 脚本运行时间 |
| 状态 | 单选 | （可自定义） |
| 招标估算 | 数字 | 万元 |
| 招标方式 | 单选 | 公开招标 / 邀请招标 |
| 资格审查方式 | 单选 | 资格后审 / 资格预审 |
| 递交方式 | 单选 | 线上递交 / 线下递交 |

## 深圳交易集团 API

### 列表 API

```
POST https://www.szexgrp.com/cms/api/v1/trade/content/page
```

请求体：
```json
{
  "modelId": 1378,
  "channelId": 2851,
  "fields": [{"fieldName": "jygg_gglxmc_rank1", "fieldValue": "招标公告"}],
  "releaseTimeBegin": "2026-04-19",
  "releaseTimeEnd": "2026-04-22",
  "page": 0,
  "size": 50
}
```

### 详情 API

```
GET https://www.szexgrp.com/cms/api/v1/trade/content/detail?contentId=XXXXX
```

详情字段从 `txt` 字段的 HTML 中通过正则提取：
- `投标文件递交截止时间` → 投标截止时间
- `本次发包工程估价 X 万元` → 招标估算
- `公开招标` / `邀请招标` → 招标方式
- `资格后审` / `资格预审` → 资格审查方式
- `线上递交` / `线下递交` → 递交方式
- `本次招标内容` → 招标概况

详见 `references/api-fields.md`