# TKMgt 检验管理平台 - 使用指南

## 快速开始

### 1. 登录

用户需要提供手机号和短信验证码：

```
/tkmgt login 手机号 验证码
```

或者让 Agent 提示输入。

### 2. Agent 操作流程

Agent 收到登录信息后：

```python
import sys
sys.path.insert(0, '/vol2/@apphome/trim.openclaw/data/workspace/skills/tkmgt/scripts')
from login import TKMgtLogin

login = TKMgtLogin()
success, result = login.login(phone='手机号', verify_code='验证码')
if success:
    login.save_session()
    print(f"登录成功: {result['userName']}")
else:
    print(f"登录失败: {result}")
```

### 3. Session 过期处理

Agent 收到 401 或无权限响应时，自动提示用户重新登录。

## Agent 指令参考

| 指令 | 说明 |
|------|------|
| 登录 | 提供手机号+验证码登录 |
| 查委托 | 查询委托台账列表 |
| 查报告 | 查询报告状态 |
| 导出 | 导出 Excel 数据 |

## Session 文件位置

`/vol2/@apphome/trim.openclaw/data/workspace/skills/tkmgt/config/session.json`

## 登录 API 详情

```
POST /TKMgt/userManagement/loginUserByMobile.do
Content-Type: application/json

{
  "mobile": "13760447009",
  "verifyCode": "839707",
  "module": "5"
}
```

成功响应：
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

## 主要模块菜单

- **委托台账** /preOrderform/queryPreOrderformList.do
- **样品台账** /sample/querySampleList.do
- **报告编制** /reportCompile/queryReportCompile.do
- **合同管理** /orderform/openingData.do
- **财务管理** /invoice/getFinanceView.do
- **经营管理** /dashBoard/getProdBusiness.do
