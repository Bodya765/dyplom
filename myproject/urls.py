from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from announcements import views
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    # Панель адміністратора
    path('admin/', admin.site.urls),
    path('', include('announcements.urls', namespace='announcements')),

                  # Головна сторінка
    path('', views.home, name='home'),

    # Аутентифікація та авторизація
    path('auth/', include('social_django.urls', namespace='social')),
    path('chat/', include('chat.urls')),
    path('support/', include('support.urls', namespace='support')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
