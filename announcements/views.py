from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.core.paginator import Paginator
from rest_framework import viewsets  # Import the viewsets module
from .models import Announcement, Category
from .forms import AnnouncementForm, ReviewForm
from .serializers import AnnouncementSerializer

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer

def profile(request):
    return render(request, 'profile.html')

def home(request):
    announcements = Announcement.objects.all()
    paginator = Paginator(announcements, 10)  # Paginate announcements
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'announcements/home.html', {'announcements': page_obj})

def announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    reviews = announcement.reviews.all()
    average_rating = announcement.average_rating()
    return render(request, 'announcements/announcement_detail.html', {
        'announcement': announcement,
        'reviews': reviews,
        'average_rating': average_rating,
    })

def add_review(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.announcement = announcement
            review.save()
            return redirect('announcement_detail', pk=announcement.pk)
    else:
        form = ReviewForm()
    return render(request, 'announcements/add_review.html', {
        'form': form,
        'announcement': announcement,
    })

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'account/login.html', {'form': form})

def create_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = AnnouncementForm()
    return render(request, 'announcements/create_announcement.html', {'form': form})

def search(request):
    query = request.GET.get('query', '')
    if query:
        results = Announcement.objects.filter(title__icontains=query)
    else:
        results = Announcement.objects.all()

    paginator = Paginator(results, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'announcements/search_results.html', {'results': page_obj})

def category_detail(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    announcements = Announcement.objects.filter(category=category)

    paginator = Paginator(announcements, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'announcements/category_detail.html', {
        'category': category,
        'announcements': page_obj,
    })

def about_us(request):
    return render(request, 'about_us.html')

def terms(request):
    return render(request, 'terms.html')

def privacy(request):
    return render(request, 'privacy.html')

def signup_view(request):
    # Signup logic can be implemented here
    return render(request, 'signup.html')
