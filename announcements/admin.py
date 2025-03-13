from django.contrib import admin
from .models import Announcement, Review, Location,Category

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'formatted_price', 'category', 'location', 'author', 'created_at', 'price')  # Add 'price' here
    search_fields = ('title', 'description')
    list_filter = ('category', 'location', 'author', 'price')  # Include price in list_filter
    list_editable = ('price',)  # Keep 'price' editable if you want
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'author')  # Make fields readonly

    def formatted_price(self, obj):
        return f"{obj.price} грн"
    formatted_price.short_description = 'Ціна'

# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description')
#     search_fields = ('name',)
#     ordering = ('name',)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'user', 'rating', 'text', 'created_at')
    search_fields = ('text', 'user__username')
    list_filter = ('rating', 'announcement', 'created_at')

class LocationAdmin(admin.ModelAdmin):
    list_display = ('name','district')

admin.site.register(Location, LocationAdmin)
admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(Category)
admin.site.register(Review, ReviewAdmin)

