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

    # API для оголошень
    path('api/', include('announcements.urls')),


]
