# chat/consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Chat, Message, UserStatus

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Обробляє підключення користувача до WebSocket чату."""
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']

        # Перевіряємо, чи користувач автентифікований
        if not self.user.is_authenticated:
            logger.warning(f"Невідомий користувач намагався підключитися до чату {self.chat_id}")
            await self.close()
            return

        # Перевіряємо, чи користувач має доступ до чату
        chat = await self.get_chat()
        if not chat:
            logger.warning(f"Чат {self.chat_id} не існує")
            await self.close()
            return

        participants = await self.get_chat_participants(chat)
        if self.user not in participants:
            logger.warning(f"Користувач {self.user.username} намагався підключитися до чату {self.chat_id} без дозволу")
            await self.close()
            return

        # Додаємо користувача до групи чату
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )

        # Оновлюємо статус користувача
        await self.set_user_online(True)

        # Отримуємо отримувача і сповіщаємо про статус
        receiver = await self.get_receiver(chat)
        if receiver:
            await self.notify_status(receiver, True)

        await self.accept()
        logger.info(f"Користувач {self.user.username} підключився до чату {self.chat_id}")

    async def disconnect(self, close_code):
        """Обробляє відключення користувача від WebSocket чату."""
        if hasattr(self, 'chat_group_name'):
            await self.channel_layer.group_discard(
                self.chat_group_name,
                self.channel_name
            )

            # Оновлюємо статус користувача
            await self.set_user_online(False)

            # Отримуємо чат і отримувача
            chat = await self.get_chat()
            if chat:
                receiver = await self.get_receiver(chat)
                if receiver:
                    await self.notify_status(receiver, False)

        logger.info(f"Користувач {self.user.username} від’єднався від чату {self.chat_id} з кодом {close_code}")

    async def receive(self, text_data):
        """Обробляє отримані WebSocket-повідомлення."""
        try:
            text_data_json = json.loads(text_data)
            logger.debug(f"Отримано WebSocket-повідомлення у чаті {self.chat_id}: {text_data_json}")
        except json.JSONDecodeError as e:
            logger.error(f"Невірний формат даних у WebSocket для чату {self.chat_id}: {text_data}. Помилка: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Невірний формат даних'
            }))
            return

        message_type = text_data_json.get('type')

        if message_type == 'typing':
            stop = text_data_json.get('stop', False)
            if not stop:
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'typing_message',
                        'sender': self.user.username,
                        'stop': stop
                    }
                )
        elif message_type == 'message':
            message = text_data_json.get('message')
            image = text_data_json.get('image')  # Це URL зображення
            message_id = text_data_json.get('message_id')

            if not message_id:
                logger.error(f"Отримано повідомлення без message_id у чаті {self.chat_id}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Відсутній message_id'
                }))
                return

            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'image': image,
                    'sender': self.user.username,
                    'timestamp': text_data_json.get('timestamp'),
                    'message_id': message_id,
                }
            )

            chat = await self.get_chat()
            if chat:
                receiver = await self.get_receiver(chat)
                if receiver:
                    await self.notify_user(receiver, self.user.username, message or "Надіслано фото")
        elif message_type == 'edit_message':
            message_id = text_data_json.get('message_id')
            new_content = text_data_json.get('content')
            edited_at = text_data_json.get('edited_at', timezone.now().isoformat())

            if not message_id or not new_content:
                logger.error(f"Неповні дані для редагування повідомлення у чаті {self.chat_id}: {text_data_json}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Неповні дані для редагування: відсутній message_id або content'
                }))
                return

            # Перевіряємо, чи message_id є числом
            try:
                message_id = int(message_id)
            except (ValueError, TypeError):
                logger.error(f"Невірний формат message_id у чаті {self.chat_id}: {message_id}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Невірний формат message_id: має бути числом'
                }))
                return

            message_obj = await self.edit_message_in_db(message_id, new_content, edited_at)

            if message_obj:
                logger.info(f"Повідомлення {message_id} успішно відредаговано у чаті {self.chat_id}")
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'edit_message_broadcast',
                        'message_id': message_id,
                        'content': new_content,
                        'edited_at': edited_at,
                    }
                )
            else:
                logger.warning(f"Не вдалося відредагувати повідомлення {message_id} у чаті {self.chat_id}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Не вдалося відредагувати повідомлення: перевірте, чи повідомлення існує і належить вам'
                }))

    async def chat_message(self, event):
        """Надсилає повідомлення учасникам чату."""
        message = await self.get_message(event['message_id'])
        if message is None:
            logger.error(f"Повідомлення з ID {event['message_id']} не знайдено у чаті {self.chat_id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Повідомлення з ID {event["message_id"]} не знайдено',
            }))
            return

        # Перевіряємо, чи відправник повідомлення не є поточним користувачем
        sender = await self.get_message_sender(message)
        if sender != self.user and not message.is_read:
            await self.mark_message_as_read(message)

        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'image': event['image'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
            'is_read': message.is_read,
            'read_at': message.read_at.isoformat() if message.read_at else None,
        }))

    async def typing_message(self, event):
        """Надсилає повідомлення про статус набору тексту."""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender': event['sender'],
            'stop': event.get('stop', False)
        }))

    async def status_message(self, event):
        """Надсилає повідомлення про статус користувача (онлайн/офлайн)."""
        await self.send(text_data=json.dumps({
            'type': 'status',
            'username': event['username'],
            'is_online': event['is_online'],
        }))

    async def edit_message_broadcast(self, event):
        """Надсилає оновлення відредагованого повідомлення учасникам чату."""
        await self.send(text_data=json.dumps({
            'type': 'edit_message',
            'message_id': event['message_id'],
            'content': event['content'],
            'edited_at': event['edited_at'],
        }))

    async def notify_user(self, user, sender_username, message):
        """Надсилає сповіщення користувачу про нове повідомлення."""
        channel_layer = get_channel_layer()
        try:
            await channel_layer.group_send(
                f'notifications_{user.id}',
                {
                    'type': 'notification_message',
                    'message': f'Нове повідомлення від {sender_username}: {message}',
                    'chat_id': self.chat_id,
                }
            )
        except Exception as e:
            logger.error(f"Помилка при відправці сповіщення користувачу {user.id}: {str(e)}")

    async def notify_status(self, user, is_online):
        """Сповіщає про зміну статусу користувача (онлайн/офлайн)."""
        channel_layer = get_channel_layer()
        try:
            await channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'status_message',
                    'username': self.user.username,
                    'is_online': is_online,
                }
            )
        except Exception as e:
            logger.error(f"Помилка при сповіщенні про статус користувача {self.user.username}: {str(e)}")

    @database_sync_to_async
    def get_chat(self):
        """Отримує чат із бази даних за ID."""
        try:
            return Chat.objects.get(id=self.chat_id)
        except Chat.DoesNotExist:
            logger.error(f"Чат {self.chat_id} не знайдено")
            return None

    @database_sync_to_async
    def get_chat_participants(self, chat):
        """Повертає учасників чату (покупець і продавець)."""
        return [chat.buyer, chat.seller]

    @database_sync_to_async
    def get_receiver(self, chat):
        """Визначає отримувача повідомлення (той, хто не є відправником)."""
        return chat.buyer if chat.seller == self.user else chat.seller

    @database_sync_to_async
    def edit_message_in_db(self, message_id, new_content, edited_at):
        """Редагує повідомлення у базі даних."""
        try:
            message = Message.objects.get(id=message_id)
            if message.sender != self.user:
                logger.warning(f"Користувач {self.user.username} намагався редагувати повідомлення {message_id}, яке йому не належить")
                return None

            # Оновлюємо вміст, час редагування та статус редагування
            message.set_content(new_content)
            message.edited_at = timezone.datetime.fromisoformat(edited_at)
            message.is_edited = True
            message.save()
            logger.info(f"Користувач {self.user.username} відредагував повідомлення {message_id} у чаті {self.chat_id}")
            return message
        except Message.DoesNotExist:
            logger.error(f"Повідомлення {message_id} не знайдено для редагування у чаті {self.chat_id}")
            return None
        except ValueError as e:
            logger.error(f"Невірний формат edited_at для повідомлення {message_id} у чаті {self.chat_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Помилка при редагуванні повідомлення {message_id} у чаті {self.chat_id}: {str(e)}")
            return None

    @database_sync_to_async
    def get_message(self, message_id):
        """Отримує повідомлення з бази даних за ID."""
        try:
            return Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            logger.error(f"Повідомлення {message_id} не знайдено у чаті {self.chat_id}")
            return None

    @database_sync_to_async
    def get_message_sender(self, message):
        """Отримує відправника повідомлення."""
        return message.sender

    @database_sync_to_async
    def mark_message_as_read(self, message):
        """Позначає повідомлення як прочитане і оновлює час прочитання."""
        try:
            message.is_read = True
            message.read_at = timezone.now()
            message.save()
            logger.info(f"Повідомлення {message.id} у чаті {self.chat_id} позначено як прочитане користувачем {self.user.username}")
        except Exception as e:
            logger.error(f"Помилка при позначенні повідомлення {message.id} як прочитаного у чаті {self.chat_id}: {str(e)}")

    @database_sync_to_async
    def set_user_online(self, is_online):
        """Оновлює статус користувача (онлайн/офлайн)."""
        try:
            status, created = UserStatus.objects.get_or_create(user=self.user)
            status.is_online = is_online
            status.last_seen = timezone.now()
            status.save()
            logger.debug(f"Статус користувача {self.user.username} оновлено: is_online={is_online}")
        except Exception as e:
            logger.error(f"Помилка при оновленні статусу користувача {self.user.username}: {str(e)}")

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Обробляє підключення до WebSocket для сповіщень."""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user = self.scope['user']
        self.notification_group_name = f'notifications_{self.user_id}'

        # Перевіряємо, чи користувач автентифікований і чи user_id відповідає користувачу
        if not self.user.is_authenticated or str(self.user.id) != self.user_id:
            logger.warning(f"Користувач {self.user.username} намагався підключитися до сповіщень {self.user_id} без дозволу")
            await self.close()
            return

        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"Користувач {self.user.username} підключився до сповіщень {self.user_id}")

    async def disconnect(self, close_code):
        """Обробляє відключення від WebSocket для сповіщень."""
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
        logger.info(f"Користувач {self.user.username} від’єднався від сповіщень {self.user_id} з кодом {close_code}")

    async def notification_message(self, event):
        """Надсилає сповіщення користувачу."""
        try:
            await self.send(text_data=json.dumps({
                'message': event['message'],
                'chat_id': event['chat_id'],
            }))
        except Exception as e:
            logger.error(f"Помилка при відправці сповіщення користувачу {self.user_id}: {str(e)}")