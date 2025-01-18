import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from utils.utils_jwt import generate_jwt_token, check_jwt_token
import time

class RefreshTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 获取 token
        token = request.headers.get('Authorization', None)
        self.new_token = None  # 初始化新 token
        if token:
            token = token.split(' ')[1] if ' ' in token else token
            payload = check_jwt_token(token)
            if payload:
                # 检查 token 是否接近过期
                exp = payload.get('exp', 0)
                time_left = exp - int(time.time())
                if time_left < 300:  # 如果 token 剩余有效期小于5分钟，则刷新
                    username = payload['username']
                    new_token = generate_jwt_token(username)
                    self.new_token = new_token  # 修改响应头部添加新 token

    def process_response(self, request, response):
        # 如果需要刷新 token，则添加新 token 到响应头部
        if self.new_token:
            response['New Authorization'] = f'{self.new_token}'
        return response
        
    