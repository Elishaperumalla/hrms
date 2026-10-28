
from django.urls import path
from . import views
from . import meet_views

app_name = "chat"

urlpatterns = [
    path("", views.chat_home, name="home"),

    # Existing POST endpoint used by the home-page modal
    path("meet/connect/", meet_views.google_meet_connect, name="meet_connect"),
    path("meet/oauth/callback/", meet_views.google_meet_callback, name="meet_oauth_callback"),
    path("meet/create/", meet_views.google_meet_create, name="meet_create"),
    path("meet/schedule/", meet_views.google_meet_schedule, name="meet_schedule"),
    path("presence/heartbeat/", views.presence_heartbeat, name="presence_heartbeat"),
    path("presence/leave/", views.presence_leave, name="presence_leave"),
    path("create/", views.create_conversation, name="create"),

    # Optional standalone create page
    path("new/", views.create_conversation_page, name="create_page"),

    path("<int:conversation_id>/", views.chat_room, name="room"),
]
