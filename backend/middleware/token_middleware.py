import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import time

class RefreshTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        pass
    def process_response(self, request, response):
        return response
        
    