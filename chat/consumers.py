import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from .models import ChatRoom, Message, UserStatus


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Перевірка, чи користувач є учасником чату
        is_participant = await self.is_room_participant(self.room_name, self.user.id)
        if not is_participant:
            await self.close()
            return

        # Додаємо користувача до групи каналів
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Встановлюємо статус користувача як онлайн
        await self.set_user_status(self.user.id, True)

        # Сповіщаємо інших учасників, що користувач онлайн
        other_participant = await self.get_other_participant(self.room_name, self.user.id)
        if other_participant:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_status",
                    "user_id": self.user.id,
                    "status": "online"
                }
            )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name') and hasattr(self, 'user') and self.user.is_authenticated:
            # Встановлюємо статус користувача як офлайн
            await self.set_user_status(self.user.id, False)

            # Сповіщаємо інших учасників, що користувач офлайн
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_status",
                    "user_id": self.user.id,
                    "status": "offline"
                }
            )

            # Видаляємо користувача з групи каналів
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "message")

        if message_type == "message":
            message = text_data_json["message"]
            # Зберігаємо повідомлення у базі даних
            saved_message = await self.save_message(
                room_id=self.room_name,
                sender_id=self.user.id,
                message=message
            )

            # Відправляємо повідомлення у групу
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender_id": self.user.id,
                    "sender_username": self.user.username,
                    "timestamp": saved_message["timestamp"].isoformat()
                }
            )
        elif message_type == "typing":
            typing_status = text_data_json["is_typing"]
            # Встановлюємо статус "набирає текст"
            other_participant = await self.get_other_participant(self.room_name, self.user.id)
            if other_participant:
                typing_to_user_id = other_participant if typing_status else None
                await self.set_typing_status(self.user.id, typing_to_user_id)

            # Відправляємо статус "набирає текст" у групу
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_status",
                    "user_id": self.user.id,
                    "is_typing": typing_status
                }
            )
        elif message_type == "read_messages":
            # Позначаємо повідомлення як прочитані
            await self.mark_messages_as_read(self.room_name, self.user.id)

            # Сповіщаємо про прочитані повідомлення
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "messages_read",
                    "user_id": self.user.id
                }
            )

    async def chat_message(self, event):
        # Відправляємо повідомлення клієнту
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"],
            "sender_id": event["sender_id"],
            "sender_username": event["sender_username"],
            "timestamp": event["timestamp"]
        }))

    async def typing_status(self, event):
        # Відправляємо статус "набирає текст" клієнту
        await self.send(text_data=json.dumps({
            "type": "typing",
            "user_id": event["user_id"],
            "is_typing": event["is_typing"]
        }))

    async def user_status(self, event):
        # Відправляємо статус користувача клієнту
        await self.send(text_data=json.dumps({
            "type": "status",
            "user_id": event["user_id"],
            "status": event["status"]
        }))

    async def messages_read(self, event):
        # Відправляємо інформацію про прочитані повідомлення
        await self.send(text_data=json.dumps({
            "type": "messages_read",
            "user_id": event["user_id"]
        }))

    @database_sync_to_async
    def save_message(self, room_id, sender_id, message):
        room = ChatRoom.objects.get(id=room_id)
        sender = User.objects.get(id=sender_id)
        message = Message.objects.create(
            room=room,
            sender=sender,
            content=message
        )
        # Оновлюємо час останнього оновлення чату
        room.updated_at = timezone.now()
        room.save()

        return {
            "id": message.id,
            "timestamp": message.timestamp
        }

    @database_sync_to_async
    def is_room_participant(self, room_id, user_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
            return room.participants.filter(id=user_id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def get_other_participant(self, room_id, user_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
            other_user = room.participants.exclude(id=user_id).first()
            return other_user.id if other_user else None
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def set_user_status(self, user_id, is_online):
        user_status, created = UserStatus.objects.get_or_create(user_id=user_id)
        user_status.is_online = is_online
        user_status.last_activity = timezone.now()
        user_status.save()

    @database_sync_to_async
    def set_typing_status(self, user_id, typing_to_user_id):
        user_status, created = UserStatus.objects.get_or_create(user_id=user_id)
        user_status.typing_to_user_id = typing_to_user_id
        user_status.save()

    @database_sync_to_async
    def mark_messages_as_read(self, room_id, user_id):
        # Позначаємо повідомлення як прочитані
        Message.objects.filter(
            room_id=room_id,
            sender__id__ne=user_id,
            is_read=False
        ).update(is_read=True)


class ChatListConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        # Створюємо групу для оновлень списку чатів конкретного користувача
        self.user_group_name = f"chat_list_{self.user.id}"

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        # Встановлюємо статус користувача як онлайн
        await self.set_user_status(self.user.id, True)

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name') and hasattr(self, 'user') and self.user.is_authenticated:
            # Встановлюємо статус користувача як офлайн
            await self.set_user_status(self.user.id, False)

            # Видаляємо користувача з групи каналів
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # У списку чатів не очікуємо повідомлень від клієнта
        pass

    async def chat_list_update(self, event):
        # Відправляємо оновлення списку чатів клієнту
        await self.send(text_data=json.dumps({
            "type": "chat_list_update",
            "chat_id": event["chat_id"]
        }))

    @database_sync_to_async
    def set_user_status(self, user_id, is_online):
        user_status, created = UserStatus.objects.get_or_create(user_id=user_id)
        user_status.is_online = is_online
        user_status.last_activity = timezone.now()
        user_status.save()
