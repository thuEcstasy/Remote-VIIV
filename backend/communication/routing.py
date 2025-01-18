import django
from django.urls import path

django.setup()
from . import consumer

websocket_urlpatterns = [
    path('ws/chat/', consumer.ChatConsumer.as_asgi()),
]
