from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('room/<int:room_id>/', views.room, name='room'),
    path('start_chat/<int:user_id>/', views.start_chat, name='start_chat'),

    # API endpoints
    path('api/chat_rooms/', views.chat_rooms, name='chat_rooms'),
    path('api/messages/<int:room_id>/', views.get_messages, name='get_messages'),
    path('api/mark_read/<int:room_id>/', views.mark_messages_as_read, name='mark_messages_as_read'),
]