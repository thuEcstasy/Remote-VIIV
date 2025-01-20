"""
ASGI config for VIIV project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from main.consumers import MyConsumer
from django.urls import path  # 导入 path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VIIV.settings')

application = ProtocolTypeRouter({
  "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            # 定义 WebSocket URL 路由
            path("ws/game", MyConsumer.as_asgi()),
        ])
    ),
})
