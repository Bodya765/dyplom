# chat/urls.py
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('announcement/<int:announcement_id>/start-chat/', views.start_chat, name='start_chat'),

    path('chat/<int:pk>/', views.chat_detail, name='chat_detail'),

    path('chats/', views.chat_list, name='chat_list'),

    path('unread-messages-count/', views.unread_messages_count, name='unread_messages_count'),

    path('send_message/', views.send_message, name='send_message'),
]