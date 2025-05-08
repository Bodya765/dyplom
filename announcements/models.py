from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.db.models import Avg
from django.contrib.auth.models import User

from django.db import models

class SupportRequest(models.Model):
    user_id = models.CharField(max_length=50)
    username = models.CharField(max_length=100)
    question = models.TextField()
    response = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    handled_by_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"Запит від @{self.username}: {self.question[:50]}"

    class Meta:
        verbose_name = "Запит на підтримку"
        verbose_name_plural = "Запити на підтримку"
class Location(models.Model):
    name = models.CharField(max_length=255, verbose_name="Назва")
    district = models.CharField(max_length=255, blank=True, verbose_name="Район")

    def __str__(self):
        return f"{self.name}{', ' + self.district if self.district else ''}"

    class Meta:
        verbose_name = "Місцезнаходження"
        verbose_name_plural = "Місцезнаходження"
        unique_together = ('name', 'district')

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Категорія")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Зображення")
    description = models.TextField(blank=True, verbose_name="Опис")
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name="Слаг")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"

@receiver(pre_save, sender=Category)
def set_category_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name, allow_unicode=True)
        if Category.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{instance.slug}-{instance.pk or Category.objects.count() + 1}"

class Announcement(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На модерації'),
        ('approved', 'Схвалено'),
        ('rejected', 'Відхилено'),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Опис")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Ціна",
        validators=[MinValueValidator(0)], blank=True, null=True
    )
    location = models.CharField(max_length=255, verbose_name="Місцезнаходження", blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, verbose_name="Категорія",
        related_name="announcements"
    )
    subcategory = models.CharField(max_length=100, blank=True, verbose_name="Підкатегорія")
    deal_type = models.CharField(max_length=50, blank=True, verbose_name="Тип угоди")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="announcements",
        null=True,
        blank=True
    )
    image = models.ImageField(upload_to='announcement_images/', null=True, blank=True, verbose_name="Зображення")
    rating = models.FloatField(default=0, verbose_name="Рейтинг")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )

    def __str__(self):
        return self.title

    def update_rating(self):
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        self.rating = round(avg_rating, 1) if avg_rating else 0
        self.save(update_fields=['rating'])

    def get_absolute_url(self):
        return reverse('announcements:announcement_detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Оголошення"
        verbose_name_plural = "Оголошення"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'subcategory', 'deal_type']),
            models.Index(fields=['owner']),
            models.Index(fields=['status']),
        ]

class ApartmentDetails(models.Model):
    announcement = models.OneToOneField(
        Announcement, on_delete=models.CASCADE, related_name='apartment_details',
        verbose_name="Оголошення"
    )
    seller_type = models.CharField(
        max_length=50, blank=True, verbose_name="Тип продавця",
        choices=[('Приватна особа', 'Приватна особа'), ('Бізнес', 'Бізнес')]
    )
    building_type = models.CharField(
        max_length=50, blank=True, verbose_name="Тип будинку",
        choices=[
            ('Царський', 'Царський'), ('Сталінка', 'Сталінка'), ('Хрущовка', 'Хрущовка'),
            ('Чешка', 'Чешка'), ('Гостинка', 'Гостинка'), ('Гуртожиток', 'Гуртожиток')
        ]
    )
    residential_complex = models.CharField(max_length=100, blank=True, verbose_name="Назва ЖК")
    floor = models.PositiveIntegerField(blank=True, null=True, verbose_name="Поверх")
    total_area = models.FloatField(
        blank=True, null=True, verbose_name="Загальна площа",
        validators=[MinValueValidator(10)]
    )
    kitchen_area = models.FloatField(
        blank=True, null=True, verbose_name="Площа кухні",
        validators=[MinValueValidator(5)]
    )
    wall_type = models.CharField(
        max_length=50, blank=True, verbose_name="Тип стін",
        choices=[
            ('Цегла', 'Цегла'), ('Панельний', 'Панельний'), ('Шпакоблочний', 'Шпакоблочний'),
            ('Газоблок', 'Газоблок'), ('СІП панель', 'СІП панель'), ('Інше', 'Інше')
        ]
    )
    housing_type = models.CharField(
        max_length=50, blank=True, verbose_name="Тип житла",
        choices=[('Новобудова', 'Новобудова'), ('Вторинне', 'Вторинне')]
    )
    rooms = models.CharField(
        max_length=10, blank=True, verbose_name="Кількість кімнат",
        choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4+', '4+')]
    )
    layout = models.CharField(
        max_length=50, blank=True, verbose_name="Планування",
        choices=[
            ('Студія', 'Студія'), ('Розділені', 'Розділені'), ('Суміжна,прохідна', 'Суміжна,прохідна'),
            ('Пентхаус', 'Пентхаус'), ('Багаторівнева', 'Багаторівнева'), ('Малосімейка', 'Малосімейка'),
            ('Смарт-квартира', 'Смарт-квартира'), ('Вільне планування', 'Вільне планування'),
            ('Двохстороння', 'Двохстороння')
        ]
    )
    bathroom = models.CharField(
        max_length=50, blank=True, verbose_name="Санвузол",
        choices=[('Суміжний', 'Суміжний'), ('Розділений', 'Розділений'), ('2+', '2+')]
    )
    heating = models.CharField(
        max_length=50, blank=True, verbose_name="Опалення",
        choices=[('Центральне', 'Центральне'), ('Індивідуальне', 'Індивідуальне'), ('Газове', 'Газове')]
    )
    renovation = models.CharField(
        max_length=50, blank=True, verbose_name="Ремонт",
        choices=[
            ('Євроремонт', 'Євроремонт'), ('Косметичний', 'Косметичний'), ('Без ремонту', 'Без ремонту'),
            ('Житловий стан', 'Житловий стан'), ('Авторський проект', 'Авторський проект')
        ]
    )
    furnishing = models.CharField(
        max_length=10, blank=True, verbose_name="Меблювання",
        choices=[('Так', 'Так'), ('Ні', 'Ні')]
    )
    appliances = models.JSONField(blank=True, default=list, verbose_name="Побутова техніка")
    multimedia = models.JSONField(blank=True, default=list, verbose_name="Мультимедіа")
    comfort = models.JSONField(blank=True, default=list, verbose_name="Комфорт")
    communications = models.JSONField(blank=True, default=list, verbose_name="Комунікації")
    infrastructure = models.JSONField(blank=True, default=list, verbose_name="Інфраструктура")
    landscape = models.JSONField(blank=True, default=list, verbose_name="Ландшафт")

    class Meta:
        verbose_name = "Деталі квартири"
        verbose_name_plural = "Деталі квартир"

    def __str__(self):
        return f"Деталі для {self.announcement.title}"

    def clean(self):
        if self.total_area and self.kitchen_area and self.total_area < self.kitchen_area:
            raise ValidationError("Загальна площа не може бути меншою за площу кухні.")

class Review(models.Model):
    announcement = models.ForeignKey(
        Announcement, on_delete=models.CASCADE, related_name="reviews",
        verbose_name="Оголошення"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Користувач"
    )
    text = models.TextField(verbose_name="Відгук")
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оцінка"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    def __str__(self):
        return f"Відгук від {self.user.username} ({self.rating}/5)"

    class Meta:
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки"
        unique_together = ('announcement', 'user')

@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_announcement_avg_rating(sender, instance, **kwargs):
    instance.announcement.update_rating()

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Користувач"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name="Аватар"
    )
    phone = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="Телефон"
    )

    def __str__(self):
        return f"Профіль користувача {self.user.username}"

    class Meta:
        verbose_name = "Профіль користувача"
        verbose_name_plural = "Профілі користувачів"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

