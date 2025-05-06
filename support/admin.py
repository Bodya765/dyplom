from django.contrib import admin
from .models import User, Question, Answer

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'name', 'created_at')
    search_fields = ('name',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'text', 'created_at', 'answered')
    list_filter = ('answered',)
    search_fields = ('text',)

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'is_admin', 'created_at')
    list_filter = ('is_admin',)
    search_fields = ('text',)