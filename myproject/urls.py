from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path, include
from announcements import views as announcement_views

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # Authentication URLs
    path('auth/', include('social_django.urls', namespace='social')),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Announcements API
    path('api/', include('announcements.urls')),

    # Home Page and Category Pages
    path('', announcement_views.home, name='home'),
    path('category/<slug:category_slug>/', announcement_views.category_detail, name='category_announcements'),
    path('accounts/', include('allauth.urls')),
    path('chat/', include('chat.urls')),
]
