from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, update_session_auth_hash
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from rest_framework import viewsets
from django.http import JsonResponse, Http404
from .models import Announcement, Category, Location
from .forms import AnnouncementForm, ProfileForm
from .serializers import AnnouncementSerializer


class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.select_related('category').prefetch_related('reviews').all()
    serializer_class = AnnouncementSerializer


def paginate_queryset(queryset, request, per_page=10):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    return page_obj


def profile(request):
    return render(request, 'profile.html')


def home(request):
    announcements = Announcement.objects.select_related('category').all()
    page_obj = paginate_queryset(announcements, request)
    return render(request, 'announcements/home.html', {'announcements': page_obj})


def announcement_detail(request, pk):
    try:
        announcement = Announcement.objects.prefetch_related('reviews').get(pk=pk)
    except Announcement.DoesNotExist:
        raise Http404("Оголошення не знайдено")

    reviews = announcement.reviews.all()
    average_rating = announcement.average_rating() if callable(getattr(announcement, 'average_rating', None)) else None

    return render(request, 'announcements/announcement_detail.html', {
        'announcement': announcement,
        'reviews': reviews,
        'average_rating': average_rating,
    })


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'announcements/login.html', {'form': form})


def create_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.user = request.user
            announcement.save()
            return redirect('category_detail', slug=announcement.category.slug)
    else:
        form = AnnouncementForm()

    categories = Category.objects.all()
    return render(request, 'announcements/create_announcement.html', {
        'form': form,
        'categories': categories,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    announcements = Announcement.objects.filter(category=category)
    return render(request, 'announcements/category_announcement.html', {
        'category': category,
        'announcements': announcements,
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