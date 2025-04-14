# chat/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from announcements.models import Announcement  # Імпортуємо модель Announcement

# Ініціалізація шифрування з ключем із налаштувань
cipher = Fernet(settings.ENCRYPTION_KEY)

class UserStatus(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='status',
        help_text="Користувач, якому належить цей статус"
    )
    is_online = models.BooleanField(
        default=False,
        help_text="Чи є користувач онлайн"
    )
    last_seen = models.DateTimeField(
        auto_now=True,
        help_text="Час останньої активності користувача"
    )

    def __str__(self):
        return f"{self.user.username} - {'Онлайн' if self.is_online else 'Офлайн'}"

    class Meta:
        verbose_name = "Статус користувача"
        verbose_name_plural = "Статуси користувачів"

class Chat(models.Model):
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='chats',
        help_text="Оголошення, до якого прив’язаний чат"
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='buyer_chats',
        help_text="Покупець у чаті"
    )
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='seller_chats',
        help_text="Продавець у чаті"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Час створення чату"
    )

    class Meta:
        unique_together = ('announcement', 'buyer', 'seller')
        verbose_name = "Чат"
        verbose_name_plural = "Чати"

    def __str__(self):
        return f"Чат між {self.buyer.username} і {self.seller.username} для {self.announcement.title}"

    def get_absolute_url(self):
        return reverse('chat:chat_detail', kwargs={'pk': self.pk})

class Message(models.Model):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Чат, до якого належить повідомлення"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="Відправник повідомлення"
    )
    encrypted_content = models.TextField(
        blank=True,
        null=True,
        help_text="Зашифрований вміст повідомлення"
    )
    image = models.ImageField(
        upload_to='chat_images/',
        blank=True,
        null=True,
        help_text="Зображення, прикріплене до повідомлення"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Час відправлення повідомлення"
    )
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Час останнього редагування повідомлення"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Чи прочитане повідомлення"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Час, коли повідомлення було прочитане"
    )
    is_edited = models.BooleanField(
        default=False,
        help_text="Чи було повідомлення відредаговане"
    )

    def set_content(self, content):
        """
        Шифрує і зберігає вміст повідомлення.
        """
        try:
            if content:
                self.encrypted_content = cipher.encrypt(content.encode()).decode()
            else:
                self.encrypted_content = None
        except Exception as e:
            raise ValueError(f"Помилка шифрування вмісту: {str(e)}")

    def get_content(self):
        if self.encrypted_content:
            try:
                return cipher.decrypt(self.encrypted_content.encode()).decode()
            except InvalidToken:
                raise ValueError("Невірний ключ шифрування або пошкоджені дані")
            except Exception as e:
                raise ValueError(f"Помилка розшифрування вмісту: {str(e)}")
        return None

    def __str__(self):
        return f"Повідомлення від {self.sender.username} у чаті {self.chat.id}"

    class Meta:
        verbose_name = "Повідомлення"
        verbose_name_plural = "Повідомлення"
        ordering = ['timestamp']