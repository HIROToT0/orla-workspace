#!/usr/bin/env python3
"""
TKMgt 登录模块
用法：
    from login import TKMgtLogin
    login = TKMgtLogin()
    success, result = login.login(phone='手机号', verify_code='验证码')
"""

import json
import os
import http.cookiejar

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'config')
SESSION_FILE = os.path.join(CONFIG_DIR, 'session.json')
BASE_URL = 'http://test.tkjy.com/TKMgt'


class TKMgtLogin:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or BASE_URL
        self.session = None
        self.jsessionid = None
        self.keyname = None
        self.user_info = None
        
        if HAS_REQUESTS:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
            })
        else:
            import urllib.request
            self._urllib = urllib.request
            self._cookie_jar = http.cookiejar.CookieJar()

    def login(self, phone: str, verify_code: str) -> tuple:
        """
        登录 TKMgt
        返回: (success: bool, result: dict | error_message: str)
        """
        if not phone or not verify_code:
            return False, "手机号和验证码不能为空"
        
        if HAS_REQUESTS:
            return self._login_requests(phone, verify_code)
        else:
            return self._login_urllib(phone, verify_code)

    def _login_requests(self, phone: str, verify_code: str) -> tuple:
        """使用 requests 登录"""
        try:
            # 1. 获取初始 Session
            self.session.get(self.base_url + '/', timeout=10)
            
            # 2. 发送登录请求
            login_url = f"{self.base_url}/userManagement/loginUserByMobile.do"
            payload = {
                "mobile": phone,
                "verifyCode": verify_code,
                "module": "5"
            }
            
            resp = self.session.post(
                login_url,
                json=payload,
                timeout=10
            )
            
            if resp.status_code != 200:
                return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
            
            data = resp.json()
            
            if data.get('isSuccess'):
                self.user_info = data.get('data', {}).get('kfsysUser', {})
                self.jsessionid = self.session.cookies.get('JSESSIONID', domain='test.tkjy.com')
                self.keyname = self.session.cookies.get('keyName', domain='test.tkjy.com')
                
                # 提取用户基本信息
                user_data = data.get('data', {})
                self.user_info = {
                    'userName': user_data.get('kfuserName'),
                    'userId': user_data.get('kfuserId'),
                    'siteId': user_data.get('kfuserSiteId'),
                    'companyName': user_data.get('kfsysUser', {}).get('companyName'),
                    'companyId': user_data.get('kfsysUser', {}).get('companyId'),
                    'keyName': user_data.get('keyName'),
                    'loginTime': user_data.get('time'),
                }
                return True, self.user_info
            else:
                return False, data.get('responseMsg', '登录失败')
                
        except Exception as e:
            return False, str(e)

    def _login_urllib(self, phone: str, verify_code: str) -> tuple:
        """使用 urllib 登录（备用）"""
        try:
            import urllib.request
            import urllib.parse
            
            opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(self._cookie_jar)
            )
            opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
            
            # 获取初始 session
            opener.open(self.base_url + '/')
            
            # 登录
            login_url = f"{self.base_url}/userManagement/loginUserByMobile.do"
            payload = json.dumps({
                "mobile": phone,
                "verifyCode": verify_code,
                "module": "5"
            }).encode()
            
            req = urllib.request.Request(
                login_url,
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                }
            )
            
            resp = opener.open(req)
            data = json.loads(resp.read().decode())
            
            if data.get('isSuccess'):
                # 提取 cookies
                for c in self._cookie_jar:
                    if c.name == 'JSESSIONID':
                        self.jsessionid = c.value
                    elif c.name == 'keyName':
                        self.keyname = c.value
                
                user_data = data.get('data', {})
                self.user_info = {
                    'userName': user_data.get('kfuserName'),
                    'userId': user_data.get('kfuserId'),
                    'siteId': user_data.get('kfuserSiteId'),
                    'companyName': user_data.get('kfsysUser', {}).get('companyName'),
                }
                return True, self.user_info
            else:
                return False, data.get('responseMsg', '登录失败')
                
        except Exception as e:
            return False, str(e)

    def save_session(self, path: str = None) -> bool:
        """保存 Session 到文件"""
        if not self.jsessionid:
            return False
        
        os.makedirs(CONFIG_DIR, exist_ok=True)
        save_path = path or SESSION_FILE
        
        session_data = {
            'jsessionid': self.jsessionid,
            'keyname': self.keyname,
            'user_info': self.user_info,
        }
        
        with open(save_path, 'w') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return True

    def load_session(self, path: str = None) -> bool:
        """从文件加载 Session"""
        load_path = path or SESSION_FILE
        
        if not os.path.exists(load_path):
            return False
        
        try:
            with open(load_path) as f:
                data = json.load(f)
            
            self.jsessionid = data.get('jsessionid')
            self.keyname = data.get('keyname')
            self.user_info = data.get('user_info')
            
            return bool(self.jsessionid)
        except Exception:
            return False

    def get_cookies(self) -> dict:
        """返回标准 cookie 字典"""
        if not self.jsessionid:
            return {}
        return {
            'JSESSIONID': self.jsessionid,
            'keyName': self.keyname or '',
        }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 3:
        print("用法: python3 login.py <手机号> <验证码>")
        sys.exit(1)
    
    phone, code = sys.argv[1], sys.argv[2]
    
    login = TKMgtLogin()
    success, result = login.login(phone, code)
    
    if success:
        print(f"✅ 登录成功: {result}")
        login.save_session()
        print(f"Session 已保存到: {SESSION_FILE}")
    else:
        print(f"❌ 登录失败: {result}")
