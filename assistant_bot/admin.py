from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'message', 'response', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user_id', 'message', 'response')