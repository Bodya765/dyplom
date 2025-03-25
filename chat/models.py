from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ChatRoom(models.Model):
    """Модель для чат-кімнати між двома користувачами"""
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Чат #{self.id} ({', '.join([user.username for user in self.participants.all()])})"

    def get_last_message(self):
        """Отримати останнє повідомлення в чат-кімнаті"""
        return self.messages.order_by('-timestamp').first()

    def get_other_participant(self, user):
        """Отримати іншого учасника чату (не поточного користувача)"""
        return self.participants.exclude(id=user.id).first()

    class Meta:
        verbose_name = "Чат-кімната"
        verbose_name_plural = "Чат-кімнати"


class Message(models.Model):
    """Модель для повідомлень"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

    class Meta:
        verbose_name = "Повідомлення"
        verbose_name_plural = "Повідомлення"
        ordering = ['timestamp']


class UserStatus(models.Model):
    """Модель для зберігання статусу користувача (онлайн/офлайн)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='status')
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(default=timezone.now)
    typing_to_user_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        status = "онлайн" if self.is_online else "офлайн"
        return f"{self.user.username} - {status}"

    class Meta:
        verbose_name = "Статус користувача"
        verbose_name_plural = "Статуси користувачів"
