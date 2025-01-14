from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError  # Import the missing ValidationError
import os



class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Категорія")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Зображення")
    description = models.TextField(blank=True, null=True, verbose_name="Опис")
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def __str__(self):
        return self.name

def set_category_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)

pre_save.connect(set_category_slug, sender=Category)


class Announcement(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Опис")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна", null=True, blank=True)
    location = models.CharField(max_length=255, verbose_name="Місцезнаходження", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="Категорія")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор")
    city = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    rating = models.FloatField(default=0, verbose_name="Рейтинг")
    image = models.ImageField(upload_to='announcements/', blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.title

    def update_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            total_rating = sum([review.rating for review in reviews])
            self.rating = total_rating / len(reviews)
            self.save()

    def save(self, *args, **kwargs):
        if self.pk:
            old_image = Announcement.objects.get(pk=self.pk).image
            if old_image and old_image != self.image:
                old_image_path = os.path.join(settings.MEDIA_ROOT, str(old_image))
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Оголошення"
        verbose_name_plural = "Оголошення"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['price']),
            models.Index(fields=['location']),
            models.Index(fields=['category']),
            models.Index(fields=['title']),
            models.Index(fields=['city']),
        ]


class Review(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="reviews", verbose_name="Оголошення")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Користувач")
    text = models.TextField(verbose_name="Відгук")
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)], verbose_name="Оцінка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    def __str__(self):
        return f"Відгук від {self.user} ({self.rating}/5)"

    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError("Рейтинг має бути від 1 до 5.")


@receiver(post_save, sender=Review)
def update_announcement_rating(sender, instance, **kwargs):
    instance.announcement.update_rating()


class Location(models.Model):
    announcement = models.OneToOneField(
        'Announcement', on_delete=models.CASCADE, related_name="location_detail", verbose_name="Оголошення"
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, null=True)  # Додаємо поле 'address'

    def __str__(self):
        return f"Локація для {self.announcement.title}"

