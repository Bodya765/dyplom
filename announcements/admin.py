from django.contrib import admin
from .models import Location, Category, Announcement, ApartmentDetails, Review, UserProfile,Notification

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'district']
    search_fields = ['name', 'district']
    list_filter = ['district']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'image']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['name']

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'subcategory', 'deal_type', 'price', 'created_at', 'get_owner_username']
    list_filter = ['category', 'subcategory', 'deal_type', 'created_at', 'owner']
    search_fields = ['title', 'description', 'location']
    date_hierarchy = 'created_at'  # Додаємо ієрархію дат для зручної навігації
    raw_id_fields = ['owner', 'category']  # Для великих списків зручніше вибирати через ID

    def get_owner_username(self, obj):
        return obj.owner.username if obj.owner else '-'
    get_owner_username.short_description = 'Власник'
    get_owner_username.admin_order_field = 'owner__username'

@admin.register(ApartmentDetails)
class ApartmentDetailsAdmin(admin.ModelAdmin):
    list_display = ['announcement', 'seller_type', 'building_type', 'total_area', 'kitchen_area']
    search_fields = ['announcement__title', 'residential_complex']
    list_filter = ['seller_type', 'building_type', 'housing_type']
    raw_id_fields = ['announcement']  # Зручний вибір оголошення через ID

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['announcement', 'get_user_username', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['announcement__title', 'user__username', 'text']
    raw_id_fields = ['announcement', 'user']  # Зручний вибір через ID

    def get_user_username(self, obj):
        return obj.user.username if obj.user else '-'
    get_user_username.short_description = 'Користувач'
    get_user_username.admin_order_field = 'user__username'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'phone', 'avatar']
    search_fields = ['user__username', 'phone']
    list_filter = ['phone']
    raw_id_fields = ['user']  # Зручний вибір користувача через ID

    def get_username(self, obj):
        return obj.user.username if obj.user else '-'
    get_username.short_description = 'Користувач'
    get_username.admin_order_field = 'user__username'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at', 'is_read')
    list_filter = ('is_read', 'user', 'created_at')
    search_fields = ('message', 'user__username')