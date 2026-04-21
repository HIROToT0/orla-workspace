---
name: tkmgt
description: TKMgt 检验管理平台自动化。支持短信登录、台账查询、数据导出、报告状态跟踪。登录时需要提供手机号和验证码。
metadata:
  platforms: [linux, openclaw]
  dependencies: [python3, requests]
  author: Orla
  version: 1.0.0
---

# TKMgt 检验管理平台

太科技术检验管理平台（test.tkjy.com/TKMgt）自动化工具。

## 功能特性

- ✅ **短信登录** — 自动登录，留存 Session Cookie
- ✅ **菜单查询** — 获取用户有权限的全部菜单
- ✅ **委托台账** — 查询委托记录列表
- ✅ **报告状态** — 跟踪报告进度
- ✅ **数据导出** — 导出 Excel 格式台账

## 目录结构

```
tkmgt/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── login.py                      # 登录模块
│   └── api_client.py                 # API 客户端（封装 Session）
├── config/
│   └── session.json                  # Session Cookie 存储（自动生成）
└── README.md                         # 详细使用文档
```

## 登录

### 方式一：Agent 直接操作（推荐）

Agent 收到用户提供的手机号 + 验证码后，执行：

```python
import sys
sys.path.insert(0, '/vol2/@apphome/trim.openclaw/data/workspace/skills/tkmgt/scripts')
from login import TKMgtLogin

login = TKMgtLogin()
success, result = login.login(phone='手机号', verify_code='验证码')
if success:
    login.save_session()
    print(f"登录成功: {result['userName']} @ {result['companyName']}")
else:
    print(f"登录失败: {result}")
```

### 方式二：Agent 调用已保存的 Session

```python
from login import TKMgtLogin

login = TKMgtLogin()
if login.load_session():
    # Session 有效
    print("Session 可用")
else:
    print("Session 已过期，需要重新登录")
```

## Session 管理

- Session 文件：`~/.openclaw/workspace/skills/tkmgt/config/session.json`
- `JSESSIONID` 有时效限制，过期后需要重新登录
- 建议：Agent 收到"未登录/无权限"响应时，自动提示用户重新登录

## API 调用示例

```python
import sys
sys.path.insert(0, '/vol2/@apphome/trim.openclaw/data/workspace/skills/tkmgt/scripts')
from api_client import TKMgtClient

client = TKMgtClient()
if not client.load_session():
    print("请先登录")

# 查询菜单
menus = client.get_user_menu()
print(f"共 {len(menus)} 个菜单项")

# 查询委托台账（分页）
result = client.query_preorder_list(page=1, limit=10)
print(f"第1页，共 {result.get('count', 0)} 条")
```

## 主要 API

| 模块 | API | 方法 |
|------|-----|------|
| 登录 | `/userManagement/loginUserByMobile.do` | POST (JSON) |
| 菜单 | `/userManagement/queryUserMenu.do` | GET |
| 委托列表 | `/preOrderform/queryPreOrderformList.do` | POST (JSON) |
| 委托详情 | `/preOrderform/getPreOrderformDetail.do` | POST (JSON) |
| 报告进度 | `/business/queryReportProgress.do` | POST (JSON) |
| 导出委托 | `/preOrderform/exportPreOrderformVO.do` | POST (JSON) → 文件下载 |

## 登录参数格式

```json
POST /TKMgt/userManagement/loginUserByMobile.do
Content-Type: application/json
Body: {"mobile": "13760447009", "verifyCode": "839707", "module": "5"}
```

返回：
```json
{
  "isSuccess": true,
  "responseCode": "/userManagement/getHomePageView.do",
  "responseMsg": "登陆成功！",
  "data": {
    "kfuserName": "何炜",
    "kfuserSiteId": "102",
    "kfuserId": "hewei",
    "keyName": "test.tkjy.com_104_102_hewei",
    "companyName": "太科技术"
  }
}
```

## 注意事项

- 测试环境：`http://test.tkjy.com/TKMgt`
- 验证码有效期约 5 分钟，需用户配合输入
- Session Cookie 需持续有效，崩则需重新登录
- 图像验证码暂不支持（需打码平台），仅支持短信验证码登录
