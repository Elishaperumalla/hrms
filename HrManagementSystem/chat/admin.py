
from django.contrib import admin
from .models import Conversation, ConversationMember, Message


class ConversationMemberInline(admin.TabularInline):
    model = ConversationMember
    extra = 0


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "chat_type", "company",
        "department", "branch", "created_by", "updated_at",
    )
    list_filter = ("chat_type", "company", "department", "branch")
    search_fields = ("name",)
    inlines = [ConversationMemberInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content",)
