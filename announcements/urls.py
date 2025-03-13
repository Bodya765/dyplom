from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'announcements'

router = DefaultRouter()
router.register(r'announcements', views.AnnouncementViewSet)

urlpatterns = [
    path('api/', include(router.urls)),  # Регістрація API оголошень
    path('locations/', views.location_list, name='location_list'),
    path('announcement/<int:pk>/a', views.announcement_detail, name='announcement-detail'),
    path('announcement/create/', views.create_announcement, name='announcement-create'),
    path('category_products/<int:category_id>/', views.category_announcements, name='category_products'),
    path('about-us/', views.about_us, name='about_us'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('chat/', views.chat_view, name='chat'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]
