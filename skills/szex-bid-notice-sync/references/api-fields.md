# 深圳交易集团 API 字段说明

## 列表 API

```
POST https://www.szexgrp.com/cms/api/v1/trade/content/page
```

### 请求体

```json
{
  "modelId": 1378,
  "channelId": 2851,
  "fields": [
    {"fieldName": "jygg_gglxmc_rank1", "fieldValue": "招标公告"},
    {"fieldName": "jygg_gclx", "fieldValue": "其他"}
  ],
  "releaseTimeBegin": "2026-04-09",
  "releaseTimeEnd": "2026-04-16",
  "page": 0,
  "size": 50
}
```

### 字段说明

| 参数 | 说明 | 可选值 |
|------|------|--------|
| modelId | 模式ID（建设工程） | 1378 |
| channelId | 频道ID（建设工程） | 2851 |
| jygg_gglxmc_rank1 | 公告类型 | 招标公告 / 答疑 / 补遗 / 截标信息 |
| jygg_gclx | 工程类型 | 施工 / 监理 / 勘察 / 设计 / 可研 / 货物 / 物业 / 其他 |
| releaseTimeBegin | 发布开始日期 | YYYY-MM-DD |
| releaseTimeEnd | 发布结束日期 | YYYY-MM-DD |
| page | 页码 | 0起 |
| size | 每页条数 | 最大50 |

### 响应字段

| 字段 | 说明 |
|------|------|
| id / docId | 公告唯一ID |
| title | 公告标题 |
| releaseTime | 发布时间（毫秒时间戳） |
| jygg_gclx | 工程类型 |
| jygg_gglxmc_rank1 | 公告类型 |

## 详情 API

```
GET https://www.szexgrp.com/cms/api/v1/trade/content/{id}/detail
```

### 详情页字段

| 字段 | 说明 |
|------|------|
| jygg_tbsj | 投标截止时间 |
| jygg_fbgcgs | 发包工程估价（万元） |
| jygg_zbfs | 招标方式 |
| jygg_zgfs | 资格审查方式 |
| jygg_djfs | 递交方式 |
| jygg_ggnr | 招标概况 |

## 字段名对照

| API字段 | 多维表格字段 | 类型 |
|---------|-------------|------|
| title | 公告名称 | 文本 |
| detail_url | 公告链接 | 链接 |
| jygg_gglxmc_rank1 | 公告类型 | 单选 |
| jygg_gclx | 工程类型 | 单选 |
| releaseTime | 发布时间 | 日期 |
| jygg_tbsj | 投标截止时间 | 日期 |
| jygg_fbgcgs | 招标估算 | 数字 |
| jygg_zbfs | 招标方式 | 单选 |
| jygg_zgfs | 资格审查方式 | 单选 |
| jygg_djfs | 递交方式 | 单选 |
| jygg_ggnr | 招标概况 | 文本 |
| - | 抓取时间 | 日期 |
| - | 状态 | 单选 |