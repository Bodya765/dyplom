import json
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils.timezone import now
from django.contrib.auth.models import User
from .models import Message, ChatRoom, UserStatus


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get room name from URL parameters
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        # Get the authenticated user
        user = self.scope['user']

        # Check if the user is authenticated
        if user.is_authenticated:
            # Update the user's status to online
            await self.update_user_status(user, True)

        # Join the WebSocket group for the room
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        user = self.scope['user']
        if user.is_authenticated:
            # Update the user's status to offline
            await self.update_user_status(user, False)

        # Leave the WebSocket group for the room
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope['user']

        if user.is_authenticated:
            message = data['message']
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Store the message in the database
            room = await self.get_chat_room(self.room_name)
            await self.save_message(room, user, message)

            # Send the message to the room's group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': user.username,
                    'timestamp': timestamp
                }
            )

    async def chat_message(self, event):
        """Handles the incoming chat message event."""
        # Send the message data to the WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def update_user_status(self, user, status):
        """Updates the user's online status in the database."""
        UserStatus.objects.update_or_create(
            user=user,
            defaults={'is_online': status, 'last_seen': now()}
        )

        # Notify other users in the chat room about the status update
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'user_status', 'username': user.username, 'is_online': status}
        )

    async def user_status(self, event):
        """Handles the user status event."""
        # Send the user status update to the WebSocket
        await self.send(text_data=json.dumps({
            'status_update': True,
            'username': event['username'],
            'is_online': event['is_online']
        }))

    async def get_chat_room(self, room_name):
        """Fetches the ChatRoom object from the database by name."""
        try:
            return await database_sync_to_async(ChatRoom.objects.get)(name=room_name)
        except ChatRoom.DoesNotExist:
            # You can choose to handle the case where the room does not exist
            return None

    async def save_message(self, room, user, message):
        """Saves the message to the database."""
        if room:
            await database_sync_to_async(Message.objects.create)(
                room=room, user=user, text=message
            )
