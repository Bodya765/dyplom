import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Коли користувач підключається
        self.room_name = 'chatroom'
        self.room_group_name = f'chat_{self.room_name}'

        # Підключаємося до групи (room)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Коли користувач відключається
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Коли сервер отримує повідомлення від користувача
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Відправляємо повідомлення в групу (до всіх підключених клієнтів)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):
        # Отримуємо повідомлення з групи і відправляємо його клієнту
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))
