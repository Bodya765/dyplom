from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from announcements import views

urlpatterns = [
    # Панель адміністратора
    path('admin/', admin.site.urls),

    # Головна сторінка
    path('', views.home, name='home'),

    # Аутентифікація та авторизація
    path('auth/', include('social_django.urls', namespace='social')),
    path('accounts/', include([
        path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
        path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
        path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
        path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    ])),

    # API для оголошень
    path('api/', include('announcements.urls', namespace='announcements')),


]
