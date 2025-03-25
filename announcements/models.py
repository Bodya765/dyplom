from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.timezone import now


class City(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Місто")
    district = models.CharField(max_length=255, verbose_name="Район")

    def __str__(self):
        return f"{self.name}, {self.district}"


class Location(models.Model):
    name = models.CharField(max_length=255, null=True)
    district = models.CharField(max_length=255)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Місто")

    def __str__(self):
        return f"{self.name}, {self.district}"


class Chat(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buyer')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чати"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Категорія")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Зображення")
    description = models.TextField(blank=True, null=True, verbose_name="Опис")
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def __str__(self):
        return self.name

    @receiver(pre_save, sender='announcements.Category')
    def set_category_slug(sender, instance, **kwargs):
        if not instance.slug or instance.pk is None:
            instance.slug = slugify(instance.name)
        elif instance.pk:
            old_instance = Category.objects.get(pk=instance.pk)
            if old_instance.name != instance.name:
                instance.slug = slugify(instance.name)
            counter = 1
            unique_slug = instance.slug
            while Category.objects.filter(slug=unique_slug).exclude(pk=instance.pk).exists():
                unique_slug = f"{instance.slug}-{counter}"
                counter += 1
            instance.slug = unique_slug


class Announcement(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Опис")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна", null=True, blank=True)
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="Місцезнаходження")
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, verbose_name="Категорія",
                                 related_name="announcements")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор")
    rating = models.FloatField(default=0, verbose_name="Рейтинг")
    image = models.ImageField(upload_to='announcement_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if not self.pk and not self.author:
            self.author = None  # Allow admin to manually set the author

        if self.pk:
            old_instance = Announcement.objects.filter(pk=self.pk).first()
            self.delete_old_image_if_needed(old_instance)

        super().save(*args, **kwargs)

    def delete_old_image_if_needed(self, old_instance):
        if old_instance and old_instance.image and old_instance.image != self.image:
            old_instance.image.delete(save=False)

    def __str__(self):
        return self.title

    def update_rating(self):
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        self.rating = avg_rating or 0
        self.save(update_fields=['rating'])

    def clean(self):
        if self.price is not None and self.price < 0:
            raise ValidationError("Ціна не може бути від’ємною.")

    class Meta:
        verbose_name = "Оголошення"
        verbose_name_plural = "Оголошення"
        ordering = ['-created_at']


@receiver(post_delete, sender=Announcement)
def delete_announcement_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


class Review(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="reviews",
                                     verbose_name="Оголошення")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Користувач")
    text = models.TextField(verbose_name="Відгук")
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name="Оцінка"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    def __str__(self):
        return f"Відгук від {self.user} ({self.rating}/5)"

    def clean(self):
        if not (1 <= self.rating <= 5):
            raise ValidationError("Оцінка має бути між 1 і 5.")


@receiver(post_save, sender=Review)
def update_announcement_avg_rating(sender, instance, created, **kwargs):
    instance.announcement.update_rating()
