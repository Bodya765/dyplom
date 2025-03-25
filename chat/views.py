from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max, Count, Exists, OuterRef
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
import json

from .models import ChatRoom, Message, UserStatus


@login_required
def index(request):
    """Головна сторінка чатів з списком усіх чатів користувача"""
    return render(request, 'chat/index.html', {
        'user_id': request.user.id,
        'username': request.user.username,
    })


@login_required
def room(request, room_id):
    """Сторінка конкретного чату"""
    room = get_object_or_404(ChatRoom, id=room_id)

    # Перевірка, чи користувач є учасником чату
    if not room.participants.filter(id=request.user.id).exists():
        return HttpResponseForbidden("Ви не є учасником цього чату")

    other_user = room.get_other_participant(request.user)

    return render(request, 'chat/room.html', {
        'room_id': room_id,
        'user_id': request.user.id,
        'username': request.user.username,
        'other_user_id': other_user.id,
        'other_username': other_user.username,
    })


@login_required
def start_chat(request, user_id):
    """Розпочати чат з конкретним користувачем"""
    # Перевірка, чи існує користувач
    other_user = get_object_or_404(User, id=user_id)

    # Перевірка, чи не намагається користувач почати чат з самим собою
    if request.user.id == user_id:
        return HttpResponseForbidden("Не можна почати чат з самим собою")

    # Шукаємо існуючий чат між користувачами
    chat_room = ChatRoom.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()

    # Якщо чат не існує, створюємо новий
    if not chat_room:
        chat_room = ChatRoom.objects.create()
        chat_room.participants.add(request.user, other_user)

    return redirect('chat:room', room_id=chat_room.id)


@login_required
def chat_rooms(request):
    """API для отримання списку чатів користувача"""
    # Отримуємо чати користувача з найновішими повідомленнями зверху
    chat_rooms = (
        ChatRoom.objects.filter(participants=request.user)
        .annotate(last_message_time=Max('messages__timestamp'))
        .annotate(unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
        ))
        .order_by('-last_message_time')
    )

    result = []
    for room in chat_rooms:
        other_user = room.get_other_participant(request.user)
        last_message = room.get_last_message()

        # Отримуємо статус користувача
        try:
            user_status = UserStatus.objects.get(user=other_user)
            is_online = user_status.is_online
            is_typing = user_status.typing_to_user_id == request.user.id
        except UserStatus.DoesNotExist:
            is_online = False
            is_typing = False

        result.append({
            'id': room.id,
            'other_user_id': other_user.id,
            'other_username': other_user.username,
            'last_message': last_message.content if last_message else "",
            'last_message_time': last_message.timestamp if last_message else room.created_at,
            'unread_count': room.unread_count,
            'is_online': is_online,
            'is_typing': is_typing,
        })

    # Конвертуємо datetime в ISO формат для правильної серіалізації
    return JsonResponse(json.loads(json.dumps(result, cls=DjangoJSONEncoder)))


@login_required
def get_messages(request, room_id):
    """API для отримання повідомлень конкретного чату"""
    room = get_object_or_404(ChatRoom, id=room_id)

    # Перевірка, чи користувач є учасником чату
    if not room.participants.filter(id=request.user.id).exists():
        return HttpResponseForbidden("Ви не є учасником цього чату")

    # Отримуємо повідомлення
    messages = Message.objects.filter(room=room).order_by('timestamp')

    result = []
    for message in messages:
        result.append({
            'id': message.id,
            'sender_id': message.sender.id,
            'sender_username': message.sender.username,
            'content': message.content,
            'timestamp': message.timestamp,
            'is_read': message.is_read,
        })

    # Конвертуємо datetime в ISO формат для правильної серіалізації
    return JsonResponse(json.loads(json.dumps(result, cls=DjangoJSONEncoder)))


@login_required
def mark_messages_as_read(request, room_id):
    """API для позначення повідомлень як прочитаних"""
    room = get_object_or_404(ChatRoom, id=room_id)

    # Перевірка, чи користувач є учасником чату
    if not room.participants.filter(id=request.user.id).exists():
        return HttpResponseForbidden("Ви не є учасником цього чату")

    # Позначаємо повідомлення як прочитані
    updated = Message.objects.filter(
        room=room,
        is_read=False
    ).exclude(
        sender=request.user
    ).update(is_read=True)

    return JsonResponse({'status': 'success', 'updated': updated})
