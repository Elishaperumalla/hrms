from django.urls import path
from .consumers import ChatConsumer, ChatSidebarConsumer

websocket_urlpatterns = [
    path(
        "ws/chat/<int:conversation_id>/",
        ChatConsumer.as_asgi(),
        name="chat_websocket",
    ),
    path(
        "ws/chat/sidebar/",
        ChatSidebarConsumer.as_asgi(),
        name="chat_sidebar_websocket",
    ),
]
