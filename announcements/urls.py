from django.urls import path, include
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'announcements'

urlpatterns = [
    path('', views.home, name='home'),
    path('search_results/', views.search_results, name='search_results'),
    path('locations/', views.location_list, name='location_list'),
    path('api/locations/', views.location_api, name='location_api'),
    path('announcement/<int:pk>/', views.announcement_detail, name='announcement_detail'),
    path('announcement/create/', views.create_announcement, name='announcement-create'),
    path("category_products/<int:category_id>/", views.category_announcements, name="category_products"),
    path('about-us/', views.about_us, name='about_us'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/update-avatar/', views.update_avatar, name='update_avatar'),
    path('<int:pk>/edit/', views.edit_announcement, name='edit_announcement'),
    path('<int:pk>/delete/', views.delete_announcement, name='delete_announcement'),
    path('announcement/<int:announcement_id>/add_review/', views.add_review, name='add_review'),
    path('announcement/autocomplete/', views.announcement_autocomplete, name='announcement_autocomplete'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/moderate/<int:pk>/', views.moderate_announcement, name='moderate_announcement'),
    path('admin-panel/get_requests/', views.get_requests, name='get_requests'),
    path('admin-panel/update_response/', views.update_response, name='update_response'),
    path('notifications/', views.notifications, name='notifications'),
]
