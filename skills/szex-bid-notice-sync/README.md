# 深圳交易集团招标公告抓取与飞书同步

自动从深圳交易集团官网抓取招标公告，过滤关键词后同步到飞书多维表格，并支持邮件/飞书通知。

---

## 功能特性

- **双数据源**：同时抓取「建设工程」和「阳光采购」两大类招标公告
- **关键词过滤**：自动过滤检测、监测、鉴定、排查、巡查等相关公告
- **飞书同步**：自动写入飞书多维表格，自动创建缺失字段
- **多端通知**：支持邮件和飞书消息双重通知
- **去重机制**：基于公告名称去重，避免重复写入
- **详情补全**：自动提取投标截止时间、招标估算、招标方式等字段

---

## 目录结构

```
szex-bid-notice-sync/
├── SKILL.md                      # OpenClaw Skill 描述文件
├── README.md                     # 本文档
├── config/
│   ├── config.json               # 主配置（飞书多维表格 / 数据源 / 关键词）
│   ├── config.json.example        # 配置示例
│   ├── email.json                 # 邮件发送配置
│   ├── email.json.example         # 邮件配置示例
│   └── .last_keyword_new.txt     # 运行时生成：本次匹配关键词的新增记录
└── scripts/
    ├── fetch_and_sync.py          # 抓取 + 同步到飞书（主脚本）
    ├── send_email.py              # 发送邮件通知
    ├── send_feishu.py             # 发送飞书消息通知
    └── run_daily.sh               # 每日定时运行脚本
```

---

## 数据源说明

| 数据源 | channelId | 类型 | 筛选条件 |
|--------|-----------|------|----------|
| 建设工程 | 2851 | 招标公告 | 按工程类型过滤 |
| 阳光采购 | 4161 | 采购公告（工程类） | 采购方式=公开招标，项目类型=工程 |

两个数据源均以 `releaseTimeBegin / releaseTimeEnd` 时间范围筛选，`days` 参数控制回溯天数。

---

## 配置说明

### config.json

```json
{
  "app_token": "飞书多维表格AppToken",
  "table_id": "数据表ID",
  "days": 3,
  "keywords": ["检测", "监测", "鉴定", "排查", "巡查"],
  "project_types": ["其他"]
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `app_token` | 飞书多维表格的 AppToken | 必填 |
| `table_id` | 数据表的 ID（URL中 ?table= 后面的值） | 必填 |
| `days` | 回溯天数，默认 3 天 | 3 |
| `project_types` | 工程类型过滤，为空则不限制 | [] |
| `keywords` | 关键词列表，标题匹配则写入并通知 | 检测/监测/鉴定/排查/巡查 |

### email.json

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

---

## 飞书多维表格字段

脚本会自动检测并创建以下字段，如已存在则跳过：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 公告名称 | 文本 | 公告标题 |
| 公告链接 | URL | 公告详情页链接 |
| 公告类型 | 单选 | 如"招标公告" |
| 子类型 | 单选 | 子类型名称 |
| 工程类型 | 单选 | 项目类型（如"其他"） |
| 发布时间 | 日期 | 发布时间 |
| 投标截止时间 | 日期 | 投标截止时间 |
| 招标概况 | 文本 | 招标内容描述（最多500字） |
| 抓取时间 | 日期 | 抓取时间（时间戳） |
| 状态 | 单选 | 状态（初始为空） |
| 招标估算 | 数字 | 工程估价（万元） |
| 招标方式 | 单选 | 公开招标 / 邀请招标 |
| 资格审查方式 | 单选 | 资格后审 / 资格预审 |
| 递交方式 | 单选 | 线上递交 / 线下递交 |

---

## API 信息

### 深圳交易集团

| 接口 | 方法 | URL |
|------|------|-----|
| 公告列表 | POST | `https://www.szexgrp.com/cms/api/v1/trade/content/page` |
| 公告详情 | GET | `https://www.szexgrp.com/cms/api/v1/trade/content/detail` |

列表 API 请求体结构：
```json
{
  "modelId": 1378,
  "channelId": 2851,
  "fields": [{"fieldName": "jygg_gglxmc_rank1", "fieldValue": "招标公告"}],
  "releaseTimeBegin": "2026-05-20",
  "releaseTimeEnd": "2026-05-27",
  "page": 0,
  "size": 50
}
```

### 飞书

| 接口 | 说明 |
|------|------|
| `POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal` | 获取 tenant_access_token |
| `GET/POS T https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records` | 读写多维表格记录 |
| `POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id` | 发送即时消息 |

飞书应用凭证从 `~/.openclaw/openclaw.json` 自动读取（需配置 channels.feishu.appId 和 appSecret）。

---

## 使用方式

### 手动运行

```bash
# 1. 抓取 + 同步到飞书
python3 scripts/fetch_and_sync.py

# 2. 发送邮件通知（读取上一步生成的 .last_keyword_new.txt）
python3 scripts/send_email.py

# 3. 发送飞书消息（从 logs/cron.log 解析抓取结果）
python3 scripts/send_feishu.py
```

### 每日定时（run_daily.sh）

```bash
bash scripts/run_daily.sh
```

依次执行抓取 → 飞书通知 → 邮件通知。

### OpenClaw Cron 配置示例

```json
{
  "cron": [
    {
      "schedule": "0 8 * * *",
      "command": "cd /path/to/szex-bid-notice-sync && bash scripts/run_daily.sh >> logs/cron.log 2>&1"
    }
  ]
}
```

---

## 工作流程

```
┌─────────────────┐
│ fetch_and_sync  │
│ (主脚本)         │
└───────┬─────────┘
        │
        ├── 读取 config.json 配置
        ├── 调用深圳交易集团列表 API（两个数据源）
        ├── 关键词过滤 + 去重
        ├── 逐条抓取详情（投标截止时间、招标估算等）
        ├── 写入飞书多维表格
        ├── 生成 config/.last_keyword_new.txt（含匹配记录）
        └── 生成 config/.fetch_time.txt（抓取时间）
        │
        ▼
┌─────────────────┐
│ send_feishu.py  │
│ (飞书通知)       │──→ 发送飞书消息卡片
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│ send_email.py   │
│ (邮件通知)       │──→ 发送 HTML 邮件（表格+链接）
└─────────────────┘
```

---

## 日志文件

| 文件 | 说明 |
|------|------|
| `logs/cron.log` | 每日定时任务的完整输出 |
| `logs/.last_result.json` | 最近一次抓取结果的解析摘要 |
| `config/.last_keyword_new.txt` | 本次匹配关键词的新增记录（JSON格式） |
| `config/.fetch_time.txt` | 本次抓取时间 |

---

## 故障排查

### 邮件未收到
1. 检查 `config/email.json` 的 SMTP 配置是否正确
2. 确认 `config/.last_keyword_new.txt` 有数据
3. 检查垃圾邮件文件夹

### 飞书通知失败
1. 检查 `send_feishu.py` 中的 app_id / app_secret / user_id 是否正确
2. 确认飞书应用有「发送消息」权限

### 飞书多维表格写入失败
1. 确认 `config/config.json` 的 app_token / table_id 正确
2. 检查飞书应用有多维表格的读写权限
3. 确认表格字段数量未超限（飞书多维表格有字段数量上限）