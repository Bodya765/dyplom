from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnnouncementViewSet
from . import views

router = DefaultRouter()
router.register(r'announcements', AnnouncementViewSet)

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),

    # Web routes
    path('', views.home, name='home'),
    path('announcement/<int:pk>/', views.announcement_detail, name='announcement_detail'),
    path('announcement/<int:pk>/add_review/', views.add_review, name='add_review'),
    path('search/', views.search, name='search'),
    path('category/<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('about/', views.about_us, name='about_us'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('create_announcement/', views.create_announcement, name='create_announcement'),
]
