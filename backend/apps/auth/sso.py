"""
SSO Integration for WeChat Work (企业微信).
"""
import json
import time
import hashlib
import requests
from typing import Optional, Tuple, Dict
from django.conf import settings
from django.core.cache import cache


class WeChatWorkSSO:
    """
    WeChat Work (企业微信) SSO integration.

    Documentation: https://developer.work.weixin.qq.com/document/path/91025
    """

    # API endpoints
    QRCODE_URL = "https://open.work.weixin.qq.com/wwopen/sso/qrConnect"
    ACCESS_TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    USER_INFO_URL = "https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo"
    USER_DETAIL_URL = "https://qyapi.weixin.qq.com/cgi-bin/user/get"

    def __init__(self):
        self.corp_id = getattr(settings, 'WECHAT_WORK_CORP_ID', '')
        self.agent_id = getattr(settings, 'WECHAT_WORK_AGENT_ID', '')
        self.secret = getattr(settings, 'WECHAT_WORK_SECRET', '')
        self.redirect_uri = getattr(settings, 'WECHAT_WORK_REDIRECT_URI', '')

    @property
    def is_configured(self) -> bool:
        """Check if WeChat Work SSO is properly configured."""
        return bool(self.corp_id and self.agent_id and self.secret)

    def get_qrcode_url(self, state: str = None) -> str:
        """
        Generate QR code login URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            URL for QR code login page
        """
        if not state:
            state = hashlib.md5(str(time.time()).encode()).hexdigest()

        # Cache the state for verification
        cache.set(f'wechat_work_state:{state}', '1', 300)  # 5 minutes expiry

        params = {
            'appid': self.corp_id,
            'agentid': self.agent_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
        }

        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{self.QRCODE_URL}?{query_string}"

    def get_access_token(self) -> Optional[str]:
        """
        Get access token for WeChat Work API.
        Uses caching to avoid hitting rate limits.

        Returns:
            Access token or None if failed
        """
        cache_key = f'wechat_work_token:{self.corp_id}'
        token = cache.get(cache_key)

        if token:
            return token

        try:
            response = requests.get(self.ACCESS_TOKEN_URL, params={
                'corpid': self.corp_id,
                'corpsecret': self.secret,
            }, timeout=10)

            data = response.json()
            if data.get('errcode') == 0:
                token = data.get('access_token')
                expires_in = data.get('expires_in', 7200) - 200  # Buffer time
                cache.set(cache_key, token, expires_in)
                return token
            else:
                return None
        except Exception:
            return None

    def verify_state(self, state: str) -> bool:
        """Verify the state parameter to prevent CSRF attacks."""
        cache_key = f'wechat_work_state:{state}'
        if cache.get(cache_key):
            cache.delete(cache_key)
            return True
        return False

    def get_user_info(self, code: str) -> Tuple[bool, Dict]:
        """
        Get user info from WeChat Work using authorization code.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Tuple of (success, user_info_dict)
        """
        access_token = self.get_access_token()
        if not access_token:
            return False, {'error': '获取access_token失败'}

        try:
            # Step 1: Get user identity
            response = requests.get(self.USER_INFO_URL, params={
                'access_token': access_token,
                'code': code,
            }, timeout=10)

            data = response.json()
            if data.get('errcode') != 0:
                return False, {'error': data.get('errmsg', '获取用户信息失败')}

            user_id = data.get('userid') or data.get('UserId')
            if not user_id:
                # External user (not in company)
                open_id = data.get('openid') or data.get('OpenId')
                return True, {
                    'type': 'external',
                    'open_id': open_id,
                    'external_userid': data.get('external_userid'),
                }

            # Step 2: Get detailed user info for internal users
            detail_response = requests.get(self.USER_DETAIL_URL, params={
                'access_token': access_token,
                'userid': user_id,
            }, timeout=10)

            detail_data = detail_response.json()
            if detail_data.get('errcode') != 0:
                # Return basic info if detail fails
                return True, {
                    'type': 'internal',
                    'user_id': user_id,
                }

            return True, {
                'type': 'internal',
                'user_id': user_id,
                'name': detail_data.get('name', ''),
                'email': detail_data.get('email', ''),
                'mobile': detail_data.get('mobile', ''),
                'avatar': detail_data.get('avatar', ''),
                'department': detail_data.get('department', []),
                'position': detail_data.get('position', ''),
                'gender': detail_data.get('gender', 0),
            }

        except Exception as e:
            return False, {'error': str(e)}


class DingTalkSSO:
    """
    DingTalk (钉钉) SSO integration.

    Documentation: https://open.dingtalk.com/document/orgapp/scan-qr-code-to-log-on-to-third-party-websites
    """

    QRCODE_URL = "https://login.dingtalk.com/oauth2/auth"
    ACCESS_TOKEN_URL = "https://api.dingtalk.com/v1.0/oauth2/userAccessToken"
    USER_INFO_URL = "https://api.dingtalk.com/v1.0/contact/users/me"

    def __init__(self):
        self.app_key = getattr(settings, 'DINGTALK_APP_KEY', '')
        self.app_secret = getattr(settings, 'DINGTALK_APP_SECRET', '')
        self.redirect_uri = getattr(settings, 'DINGTALK_REDIRECT_URI', '')

    @property
    def is_configured(self) -> bool:
        return bool(self.app_key and self.app_secret)

    def get_qrcode_url(self, state: str = None) -> str:
        """Generate QR code login URL for DingTalk."""
        if not state:
            state = hashlib.md5(str(time.time()).encode()).hexdigest()

        cache.set(f'dingtalk_state:{state}', '1', 300)

        params = {
            'client_id': self.app_key,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid',
            'state': state,
            'prompt': 'consent',
        }

        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{self.QRCODE_URL}?{query_string}"

    def verify_state(self, state: str) -> bool:
        cache_key = f'dingtalk_state:{state}'
        if cache.get(cache_key):
            cache.delete(cache_key)
            return True
        return False

    def get_user_info(self, code: str) -> Tuple[bool, Dict]:
        """Get user info from DingTalk."""
        try:
            # Get user access token
            response = requests.post(self.ACCESS_TOKEN_URL, json={
                'clientId': self.app_key,
                'clientSecret': self.app_secret,
                'code': code,
                'grantType': 'authorization_code',
            }, timeout=10)

            data = response.json()
            if 'accessToken' not in data:
                return False, {'error': data.get('message', '获取token失败')}

            access_token = data['accessToken']

            # Get user info
            user_response = requests.get(self.USER_INFO_URL, headers={
                'x-acs-dingtalk-access-token': access_token,
            }, timeout=10)

            user_data = user_response.json()

            return True, {
                'type': 'dingtalk',
                'union_id': user_data.get('unionId', ''),
                'open_id': user_data.get('openId', ''),
                'name': user_data.get('nick', ''),
                'email': user_data.get('email', ''),
                'mobile': user_data.get('mobile', ''),
                'avatar': user_data.get('avatarUrl', ''),
            }

        except Exception as e:
            return False, {'error': str(e)}


class FeishuSSO:
    """
    Feishu (飞书) SSO integration.

    Documentation: https://open.feishu.cn/document/common-capabilities/sso/web-application-sso/qr-sdk-documentation
    """

    QRCODE_URL = "https://passport.feishu.cn/suite/passport/oauth/authorize"
    ACCESS_TOKEN_URL = "https://passport.feishu.cn/suite/passport/oauth/token"
    USER_INFO_URL = "https://passport.feishu.cn/suite/passport/oauth/userinfo"

    def __init__(self):
        self.app_id = getattr(settings, 'FEISHU_APP_ID', '')
        self.app_secret = getattr(settings, 'FEISHU_APP_SECRET', '')
        self.redirect_uri = getattr(settings, 'FEISHU_REDIRECT_URI', '')

    @property
    def is_configured(self) -> bool:
        return bool(self.app_id and self.app_secret)

    def get_qrcode_url(self, state: str = None) -> str:
        """Generate QR code login URL for Feishu."""
        if not state:
            state = hashlib.md5(str(time.time()).encode()).hexdigest()

        cache.set(f'feishu_state:{state}', '1', 300)

        params = {
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'state': state,
        }

        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{self.QRCODE_URL}?{query_string}"

    def verify_state(self, state: str) -> bool:
        cache_key = f'feishu_state:{state}'
        if cache.get(cache_key):
            cache.delete(cache_key)
            return True
        return False

    def get_user_info(self, code: str) -> Tuple[bool, Dict]:
        """Get user info from Feishu."""
        try:
            # Get access token
            response = requests.post(self.ACCESS_TOKEN_URL, data={
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri,
            }, timeout=10)

            data = response.json()
            if 'access_token' not in data:
                return False, {'error': data.get('error_description', '获取token失败')}

            access_token = data['access_token']

            # Get user info
            user_response = requests.get(self.USER_INFO_URL, headers={
                'Authorization': f'Bearer {access_token}',
            }, timeout=10)

            user_data = user_response.json()

            return True, {
                'type': 'feishu',
                'union_id': user_data.get('union_id', ''),
                'open_id': user_data.get('open_id', ''),
                'name': user_data.get('name', ''),
                'email': user_data.get('email', ''),
                'mobile': user_data.get('mobile', ''),
                'avatar': user_data.get('avatar_url', ''),
            }

        except Exception as e:
            return False, {'error': str(e)}


def get_sso_provider(provider: str):
    """Get SSO provider instance by name."""
    providers = {
        'wechat_work': WeChatWorkSSO,
        'dingtalk': DingTalkSSO,
        'feishu': FeishuSSO,
    }

    provider_class = providers.get(provider)
    if provider_class:
        return provider_class()
    return None
