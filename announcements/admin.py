from django.contrib import admin
from .models import Announcement, Review, Location, Category

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'formatted_price', 'category', 'location', 'author', 'created_at', 'price')
    search_fields = ('title', 'description')
    list_filter = ('category', 'location', 'author', 'price')
    list_editable = ('price',)  # Allows editing 'price' directly in the list
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    fields = ('title', 'description', 'price', 'category', 'location', 'author', 'image')

    def formatted_price(self, obj):
        return f"{obj.price} грн"  # Formats the price for display
    formatted_price.short_description = 'Ціна'

    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user  # Use the currently logged-in user as the author
        super().save_model(request, obj, form, change)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'user', 'rating', 'text', 'created_at')
    search_fields = ('text', 'user__username', 'announcement__title')  # Searching by review text, user username, and announcement title
    list_filter = ('rating', 'announcement', 'created_at')

class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'city')  # Adding city to the Location list display

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')  # Display name and description for Category
    search_fields = ('name',)  # Add search functionality by category name

admin.site.register(Location, LocationAdmin)
admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(Category, CategoryAdmin)  # Register Category with custom admin
admin.site.register(Review, ReviewAdmin)