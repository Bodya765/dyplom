from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from rest_framework import viewsets
from django.http import JsonResponse
from unicodedata import category
from .models import Announcement, Category, Location,Review
from .forms import AnnouncementForm, ProfileForm
from .serializers import AnnouncementSerializer
from django.http import HttpResponseRedirect
class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.select_related('category').prefetch_related('reviews').all()
    serializer_class = AnnouncementSerializer

def paginate_queryset(queryset, request, per_page=10):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    try:
        return paginator.get_page(page_number)
    except PageNotAnInteger:
        return paginator.get_page(1)
    except EmptyPage:
        return paginator.get_page(paginator.num_pages)

def profile(request):
    return render(request, 'profile.html')

def home(request):
    announcements = Announcement.objects.select_related('category').all()
    page_obj = paginate_queryset(announcements, request)
    return render(request, 'announcements/home.html', {'announcements': page_obj})

def announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    reviews = announcement.reviews.all()
    average_rating = announcement.average_rating() if hasattr(announcement, 'average_rating') else None
    return render(request, 'announcements/announcement_detail.html', {
        'announcement': announcement,
        'reviews': reviews,
        'average_rating': average_rating,
    })

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redirect to some page after login
    else:
        form = AuthenticationForm()
    return render(request, 'announcements/login.html', {'form': form})

@login_required(login_url='announcements:login')  # Redirects to the login page if the user is not authenticated
def create_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user  # Встановлюємо користувача
            announcement.save()
            return redirect('announcements:category_products', announcement.category.id)

    else:
        form = AnnouncementForm()

    categories = Category.objects.all()
    locations = Location.objects.all()

    return render(request, 'announcements/create_announcement.html', {
        'form': form,
        'categories': categories,
        'locations': locations,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    announcements = Announcement.objects.filter(category=category)
    page_obj = paginate_queryset(announcements, request)
    return render(request, 'announcements/category_announcement.html', {
        'category': category,
        'announcements': page_obj,
    })

def about_us(request):
    return render(request, 'announcements/about_us.html')

def terms(request):
    return render(request, 'announcements/terms.html')

def privacy(request):
    return render(request, 'announcements/privacy.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Реєстрація пройшла успішно!")
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'announcements/signup.html', {'form': form})

def category_announcements(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    announcements = Announcement.objects.filter(category=category)
    page_obj = paginate_queryset(announcements, request)
    return render(request, 'announcements/category_announcement.html', {
        'category': category,
        'announcements': page_obj,
    })



def chat_view(request):
    return render(request, 'chat/room.html')

def location_list(request):
    search_query = request.GET.get('search', '').strip()
    random = request.GET.get('random', None)

    if random:
        locations = Location.objects.order_by('?')[:10]
    elif search_query:
        locations = Location.objects.filter(name__icontains=search_query)[:10]
    else:
        locations = Location.objects.all()[:10]

    data = [{"name": loc.name, "district": loc.district} for loc in locations]
    return JsonResponse(data, safe=False)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль успішно оновлено.')
            return redirect('profile_edit')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'announcements/profile_edit.html', {'form': form})

@login_required
def edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)

    if request.user != announcement.author:
        return redirect('announcements:announcement-detail', pk=pk)

    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            return redirect('announcements:announcement-detail', pk=pk)
    else:
        form = AnnouncementForm(instance=announcement)

    return render(request, 'announcements/edit_announcement.html', {'form': form, 'announcement': announcement})


def delete_announcement(request, pk):
    announcement = Announcement.objects.get(pk=pk)
    category_id = announcement.category.id  # Зберігаємо ID категорії

    announcement.delete()

    return redirect('announcements:category_products', category_id=category_id)
def chat_view(request, other_user_id):
    # Логіка чату
    return render(request, 'chat/room.html')


@login_required
def add_review(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        text = request.POST.get('text')

        # Create a new review
        review = Review.objects.create(
            announcement=announcement,
            rating=rating,
            text=text,
            user=request.user
        )

        # Redirect back to the announcement detail page
        return redirect('announcement_detail', pk=announcement.id)

    return redirect('announcement_detail', pk=announcement.id)
