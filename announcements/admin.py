from django.contrib import admin
from .models import Location, Category, Announcement, ApartmentDetails, Review

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'district']
    search_fields = ['name', 'district']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'created_at', 'get_owner_username']
    list_filter = ['category', 'created_at', 'owner']
    search_fields = ['title', 'description', 'location']

    def get_owner_username(self, obj):
        return obj.owner.username
    get_owner_username.short_description = 'Власник'
    get_owner_username.admin_order_field = 'owner__username'

@admin.register(ApartmentDetails)
class ApartmentDetailsAdmin(admin.ModelAdmin):
    list_display = ['announcement', 'seller_type', 'total_area']
    search_fields = ['announcement__title']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['announcement', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['announcement__title', 'user__username', 'text']