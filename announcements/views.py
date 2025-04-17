import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from rest_framework import viewsets
from django.http import JsonResponse
from django.db.models import Q
from .models import Announcement, Category, Location, Review
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
    # Отримуємо останні переглянуті оголошення з сесії
    recent_ids = request.session.get('recent_announcements', [])
    recent_announcements = Announcement.objects.filter(id__in=recent_ids).order_by('-created_at')[:5]
    return render(request, 'announcements/home.html', {
        'recent_announcements': recent_announcements,
    })


def announcement_autocomplete(request):
    query = request.GET.get('query', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)
    # Шукаємо унікальні заголовки та описи оголошень
    announcements = Announcement.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    ).values_list('title', flat=True).distinct()[:10]
    return JsonResponse(list(announcements), safe=False)


def search_results(request):
    search_query = request.GET.get('search', '').strip()
    if search_query:
        announcements = Announcement.objects.select_related('category').filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
    else:
        announcements = Announcement.objects.select_related('category').all()
    page_obj = paginate_queryset(announcements, request)
    return render(request, 'announcements/search_results.html', {
        'announcements': page_obj,
        'search_query': search_query,
    })


def announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    reviews = announcement.reviews.all()
    average_rating = announcement.average_rating() if hasattr(announcement, 'average_rating') else None

    # Додаємо оголошення до переглянутих у сесії
    if 'recent_announcements' not in request.session:
        request.session['recent_announcements'] = []
    recent = request.session['recent_announcements']
    if pk not in recent:
        recent.append(pk)
        if len(recent) > 5:  # Обмежуємо до 5 останніх
            recent.pop(0)
    request.session['recent_announcements'] = recent
    request.session.modified = True

    return render(request, 'announcements/announcement_detail.html', {
        'announcement': announcement,
        'reviews': reviews,
        'average_rating': average_rating,
    })


def login_view(request):
    if request.method == 'POST':
        # Перевірка reCAPTCHA
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if not recaptcha_response:
            messages.error(request, "Будь ласка, пройдіть перевірку reCAPTCHA.")
            form = AuthenticationForm(request, data=request.POST)
            return render(request, 'announcements/login.html', {'form': form})

        # Відправляємо запит до Google для перевірки reCAPTCHA
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response,
            'remoteip': request.META.get('REMOTE_ADDR')
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = response.json()

        if not result.get('success'):
            messages.error(request, "Помилка перевірки reCAPTCHA. Спробуйте ще раз.")
            form = AuthenticationForm(request, data=request.POST)
            return render(request, 'announcements/login.html', {'form': form})

        # Якщо reCAPTCHA пройдена, обробляємо форму входу
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'announcements/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')
    return redirect('home')


@login_required(login_url='announcements:login')
def create_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
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
        # Перевірка reCAPTCHA
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if not recaptcha_response:
            messages.error(request, "Будь ласка, пройдіть перевірку reCAPTCHA.")
            form = UserCreationForm(request.POST)
            return render(request, 'announcements/signup.html', {'form': form})

        # Відправляємо запит до Google для перевірки reCAPTCHA
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response,
            'remoteip': request.META.get('REMOTE_ADDR')
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = response.json()

        if not result.get('success'):
            messages.error(request, "Помилка перевірки reCAPTCHA. Спробуйте ще раз.")
            form = UserCreationForm(request.POST)
            return render(request, 'announcements/signup.html', {'form': form})

        # Якщо reCAPTCHA пройдена, обробляємо форму реєстрації
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
        'announcement': announcements.first() if announcements.exists() else None,
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
    user = request.user
    form = ProfileForm(request.POST or None, request.FILES or None, instance=user)

    if request.method == "POST":
        if form.has_changed():
            if form.is_valid():
                form.save()
                return redirect("announcements:profile_edit")

    return render(request, "announcements/profile_edit.html", {"form": form})


@login_required
def edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.user != announcement.author:
        return redirect('announcements:announcement_detail', pk=pk)

    if request.method == "POST":
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            return redirect('announcements:announcement_detail', pk=pk)
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'announcements/edit_announcement.html', {
        'form': form,
        'announcement': announcement,
    })


@login_required
def delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.user != announcement.author:
        return JsonResponse({'status': 'error', 'error': 'Ви не маєте права видаляти це оголошення.'}, status=403)

    if request.method == "POST":
        announcement.delete()
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error', 'error': 'Невірний метод запиту.'}, status=405)


@login_required
def add_review(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        text = request.POST.get('text')

        Review.objects.create(
            announcement=announcement,
            rating=rating,
            text=text,
            user=request.user
        )

        return redirect(reverse("announcements:announcement-detail", kwargs={"pk": announcement.id}))

    return redirect(reverse("announcements:announcement-detail", kwargs={"pk": announcement.id}))
def get_subcategories(request, category_id):
    subcategories = Category.objects.filter(parent_id=category_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)