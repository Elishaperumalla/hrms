
from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_home, name="home"),

    # Existing POST endpoint used by the home-page modal
    path("create/", views.create_conversation, name="create"),

    # Optional standalone create page
    path("new/", views.create_conversation_page, name="create_page"),

    path("<int:conversation_id>/", views.chat_room, name="room"),
]
