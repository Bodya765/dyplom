from django.contrib import admin
from .models import Announcement, Category, Review, Location

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'category', 'location', 'author', 'created_at')  # Додаємо 'price' в list_display
    search_fields = ('title', 'description')
    list_filter = ('category', 'location', 'author')  # Фільтрація за категорією, локацією, автором
    list_editable = ('price',)  # Додаємо можливість редагувати 'price'
    ordering = ('-created_at',)  # Сортуємо за датою створення, найновіші спочатку

    def formatted_price(self, obj):
        return f"{obj.price} грн"  # Форматуємо ціну для відображення в адмінці
    formatted_price.short_description = 'Ціна'

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)  # Пошук за назвою категорії

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'user', 'rating', 'text', 'created_at')  # Відображаємо 'text' та 'created_at'
    search_fields = ('text', 'user__username')  # Пошук за текстом та користувачем
    list_filter = ('rating', 'announcement')  # Фільтрація за рейтингом та оголошенням

class LocationAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'latitude', 'longitude', 'address')  # Тепер додаємо 'address'

admin.site.register(Location, LocationAdmin)
admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Review, ReviewAdmin)

