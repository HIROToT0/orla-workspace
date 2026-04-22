# szex-bid-notice-sync

深圳交易集团招标公告抓取 + 飞书多维表格同步

## 功能

- ✅ 抓取深圳交易集团 API 招标公告
- ✅ 按工程类型过滤（房建、市政、园林等）
- ✅ 按时间范围筛选
- ✅ 详情页解析（投标截止时间、招标估算、招标方式等）
- ✅ 增量同步（自动跳过已同步记录）
- ✅ 同步到飞书多维表格（Bitable）
- ✅ 邮件通知（新公告触发）
- ✅ 支持 `--dry-run` 测试模式

## 文件结构

```
szex-bid-notice-sync/
├── SKILL.md              # 技能说明
├── README.md             # 本文件
├── scripts/
│   └── fetch_and_sync.py # 主脚本
├── config/
│   ├── config.json.example
│   └── email.json.example
└── references/
    └── api-fields.md     # API字段说明
```

## 快速开始

### 1. 复制配置文件

```bash
cd ~/.openclaw/workspace/skills/szex-bid-notice-sync
cp config/config.json.example config/config.json
cp config/email.json.example config/email.json
```

### 2. 编辑 config/config.json

```json
{
  "app_token": "你的飞书多维表格 app_token",
  "table_id": "你的飞书多维表格 table_id",
  "feishu_token": "你的飞书 access_token"
}
```

获取方式：
- app_token: 飞书多维表格 URL 中 `/base/XXX` 的 XXX 部分
- table_id: 多维表格 → 更多 → 设置 → table_id
- feishu_token: 飞书开放平台 → 应用凭证 → tenant_access_token

### 3. 配置多维表格字段

在飞书多维表格中创建以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 公告名称 | 文本 | 主字段 |
| 公告链接 | 链接 | |
| 公告类型 | 单选 | 招标公告/答疑/补遗 |
| 工程类型 | 单选 | 施工/监理/勘察/其他 |
| 发布时间 | 日期 | |
| 投标截止时间 | 日期 | |
| 招标估算 | 数字 | 万元 |
| 招标方式 | 单选 | 公开招标/邀请招标 |
| 资格审查方式 | 单选 | 资格后审/资格预审 |
| 递交方式 | 单选 | 线上/线下 |
| 招标概况 | 文本 | |
| 抓取时间 | 日期 | |
| 状态 | 单选择 | 待跟进/已跟进 |

### 4. 运行

```bash
# 默认抓取最近7天，"其他"类型的公告
python3 scripts/fetch_and_sync.py

# 指定类型
python3 scripts/fetch_and_sync.py --types 施工,监理

# 抓取所有类型
python3 scripts/fetch_and_sync.py --all-types

# 测试模式（不写入飞书）
python3 scripts/fetch_and_sync.py --dry-run
```

### 5. 定时任务

```bash
# 每天早上9点执行
openclaw cron add \
  --name "深圳招标公告每日抓取" \
  --schedule "0 9 * * *" \
  --command "python3 ~/.openclaw/workspace/skills/szex-bid-notice-sync/scripts/fetch_and_sync.py"
```

或者手动加 crontab：
```bash
crontab -e
# 添加行：
0 9 * * * cd ~/.openclaw/workspace/skills/szex-bid-notice-sync && python3 scripts/fetch_and_sync.py >> /tmp/bid_sync.log 2>&1
```

## 深圳交易集团 API

```
POST https://www.szexgrp.com/cms/api/v1/trade/content/page
```

参数：
- `modelId`: 1378（建设工程）
- `channelId`: 2851（建设工程）
- `jygg_gglxmc_rank1`: 招标公告（筛选）
- `jygg_gclx`: 工程类型（施工/监理/勘察/设计/可研/货物/物业/其他）
- `releaseTimeBegin` / `releaseTimeEnd`: 日期范围
- `page`: 页码，从0开始
- `size`: 每页条数，最大50

详见 `references/api-fields.md`