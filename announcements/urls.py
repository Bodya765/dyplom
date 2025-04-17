from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'announcements'

router = DefaultRouter()
router.register(r'announcements', views.AnnouncementViewSet)

urlpatterns = [
    path('api/', include(router.urls)),  # Регістрація API оголошень
    path('search_results/', views.search_results, name='search_results'),
    path('locations/', views.location_list, name='location_list'),
    path('announcement/<int:pk>/', views.announcement_detail, name='announcement-detail'),
    path('announcement/create/', views.create_announcement, name='announcement-create'),
    path("api/category_products/<int:category_id>/", views.category_announcements, name="category_products"),
    path('about-us/', views.about_us, name='about_us'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('<int:pk>/edit/', views.edit_announcement, name='edit_announcement'),
    path('<int:pk>/delete/', views.delete_announcement, name='delete_announcement'),
    path('api/announcement/<int:announcement_id>/add_review/', views.add_review, name='add_review'),
    path('api/announcement/autocomplete/', views.announcement_autocomplete, name='announcement_autocomplete'),
    path('api/categories/<int:category_id>/subcategories/', views.get_subcategories, name='get_subcategories'),
]
