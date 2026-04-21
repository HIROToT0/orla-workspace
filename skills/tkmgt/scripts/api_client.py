#!/usr/bin/env python3
"""
TKMgt API 客户端
用法：
    from api_client import TKMgtClient
    client = TKMgtClient()
    client.load_session()
    menus = client.get_user_menu()
"""

import json
import os
import sys

# Add parent dir to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from login import TKMgtLogin, BASE_URL


class TKMgtClient(TKMgtLogin):
    """继承自 Login，支持已保存 Session 的 API 调用"""
    
    def __init__(self, base_url: str = None):
        super().__init__(base_url)
        self._loaded = False
    
    def load_saved_session(self) -> bool:
        """加载已保存的 Session（不触发登录）"""
        if not super().load_session():
            return False
        # Re-initialize session with saved cookies
        if HAS_REQUESTS and self.session:
            self.session.cookies.set('JSESSIONID', self.jsessionid, domain='test.tkjy.com')
            if self.keyname:
                self.session.cookies.set('keyName', self.keyname, domain='test.tkjy.com')
        self._loaded = True
        return True
    
    def _post(self, path: str, data: dict = None, params: dict = None) -> tuple:
        """发送 POST 请求，返回 (success, response_data)"""
        if not self.jsessionid:
            return False, {"error": "Not logged in"}
        
        try:
            url = f"{self.base_url}{path}"
            
            if hasattr(self, 'session') and self.session:
                # requests 方式
                headers = {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': f"{self.base_url}/",
                }
                resp = self.session.post(url, json=data, params=params, headers=headers, timeout=15)
                return True, resp.json()
            else:
                # urllib 备用
                import urllib.request
                
                opener = urllib.request.build_opener(
                    urllib.request.HTTPCookieProcessor(self._cookie_jar)
                )
                opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
                
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data or {}).encode() if data else None,
                    headers={
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Cookie': f"JSESSIONID={self.jsessionid}; keyName={self.keyname or ''}",
                    }
                )
                resp = opener.open(req, timeout=15)
                return True, json.loads(resp.read().decode())
                
        except Exception as e:
            return False, {"error": str(e)}

    def _get(self, path: str, params: dict = None) -> tuple:
        """发送 GET 请求"""
        if not self.jsessionid:
            return False, {"error": "Not logged in"}
        
        try:
            url = f"{self.base_url}{path}"
            
            if hasattr(self, 'session') and self.session:
                headers = {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': f"{self.base_url}/",
                }
                resp = self.session.get(url, params=params, headers=headers, timeout=15)
                return True, resp.json()
            else:
                import urllib.request
                
                query = ''
                if params:
                    import urllib.parse
                    query = '?' + urllib.parse.urlencode(params)
                
                opener = urllib.request.build_opener(
                    urllib.request.HTTPCookieProcessor(self._cookie_jar)
                )
                opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
                
                req = urllib.request.Request(
                    f"{url}{query}",
                    headers={
                        'X-Requested-With': 'XMLHttpRequest',
                        'Cookie': f"JSESSIONID={self.jsessionid}; keyName={self.keyname or ''}",
                    }
                )
                resp = opener.open(req, timeout=15)
                return True, json.loads(resp.read().decode())
                
        except Exception as e:
            return False, {"error": str(e)}

    # ========== API Methods ==========

    def get_user_menu(self) -> list:
        """获取用户菜单（返回菜单列表）"""
        success, data = self._get('/userManagement/queryUserMenu.do')
        if success and isinstance(data, dict):
            return data.get('data', [])
        return []

    def query_preorder_list(
        self,
        page: int = 1,
        limit: int = 10,
        search_obj: dict = None,
        **form_fields
    ) -> dict:
        """
        查询委托台账列表
        返回: {"count": N, "data": [...], "msg": "..."}
        """
        payload = {
            "page": page,
            "limit": limit,
        }
        
        if search_obj:
            payload["searchObj"] = search_obj
        
        if form_fields:
            payload.update(form_fields)
        
        # 去掉 None 值
        payload = {k: v for k, v in payload.items() if v is not None}
        
        success, data = self._post('/preOrderform/queryPreOrderformList.do', payload)
        
        if success and isinstance(data, dict):
            # layui table 格式兼容
            return {
                "count": data.get('count', 0),
                "data": data.get('data', []),
                "msg": data.get('msg', ''),
            }
        return {"count": 0, "data": [], "msg": str(data)}

    def get_entrust_detail(self, order_id: str = None, order_code: str = None) -> dict:
        """获取委托详情"""
        payload = {}
        if order_id:
            payload["id"] = order_id
        if order_code:
            payload["orderCode"] = order_code
        
        success, data = self._post('/preOrderform/getPreOrderformDetail.do', payload)
        if success:
            return data
        return {}

    def query_report_progress(self, report_code: str = None, order_code: str = None) -> dict:
        """查询报告进度"""
        payload = {}
        if report_code:
            payload["reportCode"] = report_code
        if order_code:
            payload["orderCode"] = order_code
        
        success, data = self._post('/business/queryReportProgress.do', payload)
        if success:
            return data
        return {}

    def get_dashboard(self) -> dict:
        """获取仪表盘数据（需额外参数）"""
        success, data = self._get('/dashBoard/getProdBusiness.do')
        return data if success else {}

    def export_preorder(self, export_params: dict = None) -> bytes:
        """
        导出委托台账（返回文件内容）
        注意：返回文件流，需用 content = export_preorder() 然后写文件
        """
        if not self.jsessionid:
            return b""
        
        try:
            url = f"{self.base_url}/preOrderform/exportPreOrderformVO.do"
            headers = {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'Cookie': f"JSESSIONID={self.jsessionid}; keyName={self.keyname or ''}",
            }
            
            resp = self.session.post(url, json=export_params or {}, headers=headers, timeout=30)
            return resp.content
            
        except Exception:
            return b""
    
    def is_logged_in(self) -> bool:
        """检查 Session 是否有效（通过查询菜单验证）"""
        if not self.jsessionid:
            return False
        menus = self.get_user_menu()
        return len(menus) > 0


if __name__ == '__main__':
    client = TKMgtClient()
    
    if not client.load_saved_session():
        print("❌ 未找到有效 Session，请先运行 login.py 登录")
        sys.exit(1)
    
    print(f"✅ Session 加载成功: {client.user_info}")
    
    # 测试获取菜单
    menus = client.get_user_menu()
    print(f"📋 菜单项: {len(menus)} 个")
    
    # 测试查询委托
    result = client.query_preorder_list(page=1, limit=5)
    print(f"📝 委托台账: {result.get('count', 0)} 条")
