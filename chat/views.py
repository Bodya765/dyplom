# chat/views.py
import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Chat, Message, Announcement

# Налаштування логування
logger = logging.getLogger(__name__)

@login_required
@transaction.atomic
def start_chat(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    buyer = request.user
    seller = announcement.author

    if buyer == seller:
        logger.warning(f"Користувач {buyer.username} намагався створити чат із самим собою для оголошення {announcement_id}")
        return redirect('home')

    chat = Chat.objects.filter(announcement=announcement, buyer=buyer, seller=seller).first()
    if not chat:
        chat = Chat.objects.create(announcement=announcement, buyer=buyer, seller=seller)
        logger.info(f"Створено новий чат {chat.id} між {buyer.username} і {seller.username} для оголошення {announcement_id}")

    return redirect('chat:chat_detail', pk=chat.id)

@login_required
def chat_detail(request, pk):
    chat = get_object_or_404(Chat, pk=pk)
    if request.user not in [chat.buyer, chat.seller]:
        logger.warning(f"Користувач {request.user.username} намагався отримати доступ до чату {pk} без дозволу")
        return redirect('home')

    # Позначаємо всі непрочитані повідомлення як прочитані одним запитом
    chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True, read_at=timezone.now())

    # Отримуємо повідомлення з оптимізацією (використовуємо select_related для sender)
    messages = chat.messages.select_related('sender').order_by('timestamp')

    # Групуємо повідомлення за датою
    messages_by_date = {}
    for message in messages:
        message_date = message.timestamp.date()
        if message_date not in messages_by_date:
            messages_by_date[message_date] = []
        messages_by_date[message_date].append(message)

    # Використовуємо related_name для спрощення запиту
    user_chats = (request.user.buyer_chats.all() | request.user.seller_chats.all()).select_related('buyer', 'seller', 'announcement').order_by('-created_at')

    return render(request, 'chat/chat_detail.html', {
        'chat': chat,
        'messages_by_date': messages_by_date,
        'user_chats': user_chats,
    })

@login_required
def chat_list(request):
    # Використовуємо related_name для спрощення запиту з оптимізацією
    user_chats = (request.user.buyer_chats.all() | request.user.seller_chats.all()).select_related('buyer', 'seller', 'announcement').order_by('-created_at')
    return render(request, 'chat/chat_list.html', {
        'user_chats': user_chats,
    })

@login_required
def unread_messages_count(request):
    # Оптимізуємо запит: використовуємо annotate для підрахунку
    unread_count = Message.objects.filter(
        chat__in=(request.user.buyer_chats.all() | request.user.seller_chats.all()),
        is_read=False,
    ).exclude(sender=request.user).count()

    return JsonResponse({'unread_count': unread_count})

@login_required
@require_POST
@transaction.atomic
def send_message(request):
    chat_id = request.POST.get('chat_id')
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')

    # Перевіряємо, чи передано chat_id
    if not chat_id:
        logger.error(f"Користувач {request.user.username} намагався відправити повідомлення без chat_id")
        return JsonResponse({'status': 'error', 'error': 'chat_id не вказано'}, status=400)

    # Перевіряємо, чи є хоча б текст або зображення
    if not content and not image:
        logger.warning(f"Користувач {request.user.username} намагався відправити порожнє повідомлення у чат {chat_id}")
        return JsonResponse({'status': 'error', 'error': 'Повідомлення не може бути порожнім'}, status=400)

    # Валідація розміру зображення (максимум 5 МБ)
    if image and image.size > 5 * 1024 * 1024:  # 5 МБ у байтах
        logger.warning(f"Користувач {request.user.username} намагався завантажити зображення розміром {image.size} байт, що перевищує ліміт")
        return JsonResponse({'status': 'error', 'error': 'Зображення занадто велике (максимум 5 МБ)'}, status=400)

    try:
        chat = Chat.objects.get(id=chat_id)
    except ValueError:
        logger.error(f"Невірний формат chat_id: {chat_id} для користувача {request.user.username}")
        return JsonResponse({'status': 'error', 'error': 'Невірний формат chat_id'}, status=400)
    except Chat.DoesNotExist:
        logger.error(f"Чат {chat_id} не знайдено для користувача {request.user.username}")
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
        logger.error(f"Помилка при створенні повідомлення у чаті {chat_id} для користувача {request.user.username}: {str(e)}")
        return JsonResponse({'status': 'error', 'error': 'Помилка при відправці повідомлення'}, status=500)

    return JsonResponse({
        'status': 'success',
        'message_id': message.id,
        'image_url': message.image.url if message.image else None,
        'content': message.get_content() if content else None,
    })