import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Chat, Message, Announcement

# Налаштування логування
logger = logging.getLogger(__name__)

@login_required
@transaction.atomic
def start_chat(request, announcement_id):
    """Старт нового чату для оголошення."""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    buyer = request.user
    seller = announcement.owner

    if buyer == seller:
        logger.warning(f"Користувач {buyer.username} намагався створити чат із самим собою для оголошення {announcement_id}")
        return redirect('home')

    chat, created = Chat.objects.get_or_create(
        announcement=announcement,
        buyer=buyer,
        seller=seller,
        defaults={'created_at': timezone.now()}
    )
    if created:
        logger.info(f"Створено новий чат {chat.id} між {buyer.username} і {seller.username} для оголошення {announcement_id}")
    else:
        logger.info(f"Використано існуючий чат {chat.id} між {buyer.username} і {seller.username}")

    return redirect('chat:chat_detail', pk=chat.id)

@login_required
def chat_detail(request, pk):
    """Детальна сторінка чату."""
    chat = get_object_or_404(Chat, pk=pk)
    if request.user not in [chat.buyer, chat.seller]:
        logger.warning(f"Користувач {request.user.username} намагався отримати доступ до чату {pk} без дозволу")
        return redirect('home')

    # Позначаємо непрочитані повідомлення як прочитані
    chat.messages.filter(is_read=False, sender=request.user).update(is_read=True, read_at=timezone.now())

    # Отримуємо повідомлення з оптимізацією
    messages = chat.messages.select_related('sender').order_by('timestamp')

    # Групуємо повідомлення за датою
    messages_by_date = {}
    for message in messages:
        date_key = message.timestamp.date()
        if date_key not in messages_by_date:
            messages_by_date[date_key] = []
        messages_by_date[date_key].append(message)

    # Отримуємо список чатів користувача
    user_chats = (request.user.buyer_chats.all() | request.user.seller_chats.all()) \
        .select_related('buyer', 'seller', 'announcement') \
        .order_by('-created_at')

    return render(request, 'chat/chat_detail.html', {
        'chat': chat,
        'messages_by_date': messages_by_date,
        'user_chats': user_chats,
    })

@login_required
def chat_list(request):
    """Список чатів користувача."""
    user_chats = (request.user.buyer_chats.all() | request.user.seller_chats.all()) \
        .select_related('buyer', 'seller', 'announcement') \
        .order_by('-created_at')
    return render(request, 'chat/chat_list.html', {
        'user_chats': user_chats,
    })

@login_required
def unread_messages_count(request):
    """Повертає кількість непрочитаних повідомлень."""
    user_chats = request.user.buyer_chats.all() | request.user.seller_chats.all()
    unread_count = Message.objects.filter(
        chat__in=user_chats,
        is_read=False,
    ).exclude(sender=request.user).count()
    return JsonResponse({'unread_count': unread_count})

@login_required
@require_POST
@transaction.atomic
def send_message(request):
    """Надсилання нового повідомлення у чат."""
    chat_id = request.POST.get('chat_id')
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')

    if not chat_id:
        logger.error(f"Користувач {request.user.username} намагався відправити повідомлення без chat_id")
        return JsonResponse({'status': 'error', 'error': 'chat_id не вказано'}, status=400)

    if not content and not image:
        logger.warning(f"Користувач {request.user.username} намагався відправити порожнє повідомлення у чат {chat_id}")
        return JsonResponse({'status': 'error', 'error': 'Повідомлення не може бути порожнім'}, status=400)

    if image and image.size > 5 * 1024 * 1024:  # 5 МБ
        logger.warning(f"Користувач {request.user.username} намагався завантажити зображення {image.size} байт, що перевищує ліміт")
        return JsonResponse({'status': 'error', 'error': 'Зображення занадто велике (максимум 5 МБ)'}, status=400)

    try:
        chat = Chat.objects.get(id=chat_id)
    except (ValueError, Chat.DoesNotExist):
        logger.error(f"Чат {chat_id} не знайдено або формат невірний для {request.user.username}")
        return JsonResponse({'status': 'error', 'error': 'Чат не знайдено'}, status=404)

    if request.user not in [chat.buyer, chat.seller]:
        logger.warning(f"Користувач {request.user.username} намагався відправити повідомлення у чат {chat_id} без дозволу")
        return JsonResponse({'status': 'error', 'error': 'Доступ заборонений'}, status=403)

    try:
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            image=image
        )
        if content:
            message.set_content(content)
        message.save()
        logger.info(f"Користувач {request.user.username} відправив повідомлення {message.id} у чат {chat_id}")
    except Exception as e:
        logger.error(f"Помилка при створенні повідомлення у чаті {chat_id}: {str(e)}")
        return JsonResponse({'status': 'error', 'error': 'Помилка при відправці'}, status=500)

    return JsonResponse({
        'status': 'success',
        'message_id': message.id,
        'image_url': message.image.url if message.image else None,
        'content': message.get_content() if content else None,
        'timestamp': message.timestamp.isoformat(),
    })

@login_required
@require_POST
@transaction.atomic
def edit_message(request, message_id):
    """Редагування повідомлення."""
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    data = json.loads(request.body)
    new_content = data.get('content', '').strip()

    if not new_content:
        logger.warning(f"Користувач {request.user.username} намагався відредагувати повідомлення {message_id} без контенту")
        return JsonResponse({'status': 'error', 'error': 'Контент відсутній'}, status=400)

    try:
        message.content = new_content
        message.edited_at = timezone.now()
        message.save()
        logger.info(f"Користувач {request.user.username} відредагував повідомлення {message_id}")
    except Exception as e:
        logger.error(f"Помилка при редагуванні повідомлення {message_id}: {str(e)}")
        return JsonResponse({'status': 'error', 'error': 'Помилка при редагуванні'}, status=500)

    return JsonResponse({'status': 'success', 'content': new_content, 'edited_at': message.edited_at.isoformat()})

@login_required
@require_POST
@transaction.atomic
def delete_message(request, message_id):
    """Видалення повідомлення."""
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    try:
        chat_id = message.chat.id
        message.delete()
        logger.info(f"Користувач {request.user.username} видалив повідомлення {message_id} з чату {chat_id}")
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Помилка при видаленні повідомлення {message_id}: {str(e)}")
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
@login_required
@require_POST
def save_state(request):
    data = json.loads(request.body)
    messages = data.get('messages', [])
    for msg in messages:
        message = get_object_or_404(Message, id=msg['id'], sender=request.user)
        if message.get_content() != msg['content']:
            message.set_content(msg['content'])
            message.save()
    return JsonResponse({'status': 'success'})