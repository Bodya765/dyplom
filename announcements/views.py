import requests
import json
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q
from rest_framework import viewsets
from .models import Announcement, Category, ApartmentDetails, Review, Location
from .forms import AnnouncementForm, ProfileForm, ReviewForm
from .serializers import AnnouncementSerializer

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.select_related('category', 'owner').prefetch_related('reviews').all()
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
    return render(request, 'announcements/profile.html')

def home(request):
    recent_ids = request.session.get('recent_announcements', [])
    try:
        recent_ids = [int(id) for id in recent_ids]  # Ensure IDs are integers
        recent_announcements = Announcement.objects.filter(id__in=recent_ids).select_related('category', 'owner')[:5]
    except (ValueError, TypeError):
        recent_announcements = []
    return render(request, 'announcements/home.html', {
        'recent_announcements': recent_announcements,
    })

def announcement_autocomplete(request):
    query = request.GET.get('query', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)
    announcements = Announcement.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    ).values_list('title', flat=True).distinct()[:10]
    return JsonResponse(list(announcements), safe=False)

def search_results(request):
    search_query = request.GET.get('search', '').strip()
    announcements = Announcement.objects.select_related('category', 'owner')
    if search_query:
        announcements = announcements.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query) | Q(location__icontains=search_query)
        )
    page_obj = paginate_queryset(announcements, request)
    return render(request, 'announcements/search_results.html', {
        'announcements': page_obj,
        'search_query': search_query,
    })

def announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement.objects.select_related('category', 'owner').prefetch_related('reviews'), pk=pk)
    reviews = announcement.reviews.all()
    review_form = ReviewForm(user=request.user, announcement=announcement) if request.user.is_authenticated else None

    # Add to recent announcements
    if 'recent_announcements' not in request.session:
        request.session['recent_announcements'] = []
    recent = request.session['recent_announcements']
    if pk not in recent:
        recent.append(pk)
        if len(recent) > 5:
            recent.pop(0)
    request.session['recent_announcements'] = recent
    request.session.modified = True

    return render(request, 'announcements/announcement_detail.html', {
        'announcement': announcement,
        'reviews': reviews,
        'rating': announcement.rating,
        'review_form': review_form,
    })

def login_view(request):
    if request.method == 'POST':
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if not recaptcha_response:
            messages.error(request, "Будь ласка, пройдіть перевірку reCAPTCHA.")
            form = AuthenticationForm(request, data=request.POST)
            return render(request, 'announcements/login.html', {'form': form})

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

        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Ви успішно увійшли!")
            return redirect('home')
        else:
            messages.error(request, "Невірний логін або пароль.")
    else:
        form = AuthenticationForm()
    return render(request, 'announcements/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "Ви вийшли з системи.")
    return redirect('home')

@login_required(login_url='announcements:login')
def create_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.owner = request.user
            announcement.save()

            # Save ApartmentDetails for apartments
            if announcement.subcategory == "Квартира":
                apartment_details = ApartmentDetails(
                    announcement=announcement,
                    seller_type=form.cleaned_data.get('seller_type', ''),
                    building_type=form.cleaned_data.get('building_type', ''),
                    residential_complex=form.cleaned_data.get('residential_complex', ''),
                    floor=form.cleaned_data.get('floor'),
                    total_area=form.cleaned_data.get('total_area'),
                    kitchen_area=form.cleaned_data.get('kitchen_area'),
                    wall_type=form.cleaned_data.get('wall_type', ''),
                    housing_type=form.cleaned_data.get('housing_type', ''),
                    rooms=form.cleaned_data.get('rooms', ''),
                    layout=form.cleaned_data.get('layout', ''),
                    bathroom=form.cleaned_data.get('bathroom', ''),
                    heating=form.cleaned_data.get('heating', ''),
                    renovation=form.cleaned_data.get('renovation', ''),
                    furnishing=form.cleaned_data.get('furnishing', ''),
                    appliances=form.cleaned_data.get('appliances', []),
                    multimedia=form.cleaned_data.get('multimedia', []),
                    comfort=form.cleaned_data.get('comfort', []),
                    communications=form.cleaned_data.get('communications', []),
                    infrastructure=form.cleaned_data.get('infrastructure', []),
                    landscape=form.cleaned_data.get('landscape', []),
                )
                try:
                    apartment_details.full_clean()
                    apartment_details.save()
                except ValidationError as e:
                    messages.error(request, f"Помилка у деталях квартири: {e}")
                    return render(request, 'announcements/create_announcement.html', {
                        'form': form,
                        'categories': Category.objects.all(),
                    })

            # Telegram bot notification
            try:
                bot_token = settings.TELEGRAM_BOT_TOKEN
                chat_id = settings.TELEGRAM_CHAT_ID
                message = (
                    f"Нове оголошення: {announcement.title}\n"
                    f"Ціна: {announcement.price or 'Не вказано'} грн\n"
                    f"Місцезнаходження: {announcement.location or 'Не вказано'}\n"
                    f"Категорія: {announcement.category.name if announcement.category else 'Не вказано'}\n"
                )
                if announcement.subcategory == "Квартира" and hasattr(announcement, 'apartment_details'):
                    details = announcement.apartment_details
                    if details.total_area:
                        message += f"Площа: {details.total_area} м²\n"
                    if details.seller_type:
                        message += f"Тип продавця: {details.seller_type}\n"
                requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    data={'chat_id': chat_id, 'text': message}
                )
            except Exception as e:
                print(f"Помилка відправки в Telegram: {e}")

            messages.success(request, "Оголошення успішно створено!")
            return redirect('announcements:announcement-detail', pk=announcement.pk)
        else:
            messages.error(request, "Помилка у формі. Перевірте введені дані.")
    else:
        form = AnnouncementForm()
    categories = Category.objects.all()
    return render(request, 'announcements/create_announcement.html', {
        'form': form,
        'categories': categories,
    })

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    announcements = Announcement.objects.filter(category=category).select_related('owner')
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
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if not recaptcha_response:
            messages.error(request, "Будь ласка, пройдіть перевірку reCAPTCHA.")
            form = UserCreationForm(request.POST)
            return render(request, 'announcements/signup.html', {'form': form})

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

        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Реєстрація пройшла успішно!")
            return redirect('home')
        else:
            messages.error(request, "Помилка у формі реєстрації. Перевірте введені дані.")
    else:
        form = UserCreationForm()
    return render(request, 'announcements/signup.html', {'form': form})

def category_announcements(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    announcements = Announcement.objects.filter(category=category).select_related('owner')
    page_obj = paginate_queryset(announcements, request)
    return render(request, 'announcements/category_announcement.html', {
        'category': category,
        'announcements': page_obj,
        'announcement': announcements.first() if announcements.exists() else None,
    })

def chat_view(request):
    # Placeholder for chat system integration
    return render(request, 'chat/room.html')

def location_list(request):
    search_query = request.GET.get('search', '').strip()
    random = request.GET.get('random', None)
    locations = []
    if random:
        locations = Location.objects.order_by('?')[:10]
    elif search_query:
        locations = Location.objects.filter(
            Q(name__icontains=search_query) | Q(district__icontains=search_query)
        )[:10]
    else:
        locations = Location.objects.all()[:10]
    data = [{"name": loc.name, "district": loc.district} for loc in locations]
    return JsonResponse(data, safe=False)

@login_required
def profile_edit(request):
    user = request.user
    form = ProfileForm(request.POST or None, request.FILES or None, instance=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Профіль успішно оновлено!")
        return redirect("announcements:profile_edit")
    return render(request, "announcements/profile_edit.html", {"form": form})

@login_required
def edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.user != announcement.owner:
        messages.error(request, "Ви не маєте права редагувати це оголошення.")
        return redirect('announcements:announcement-detail', pk=pk)

    if request.method == "POST":
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            announcement = form.save()
            # Update ApartmentDetails
            if announcement.subcategory == "Квартира":
                details, created = ApartmentDetails.objects.get_or_create(announcement=announcement)
                details.seller_type = form.cleaned_data.get('seller_type', '')
                details.building_type = form.cleaned_data.get('building_type', '')
                details.residential_complex = form.cleaned_data.get('residential_complex', '')
                details.floor = form.cleaned_data.get('floor')
                details.total_area = form.cleaned_data.get('total_area')
                details.kitchen_area = form.cleaned_data.get('kitchen_area')
                details.wall_type = form.cleaned_data.get('wall_type', '')
                details.housing_type = form.cleaned_data.get('housing_type', '')
                details.rooms = form.cleaned_data.get('rooms', '')
                details.layout = form.cleaned_data.get('layout', '')
                details.bathroom = form.cleaned_data.get('bathroom', '')
                details.heating = form.cleaned_data.get('heating', '')
                details.renovation = form.cleaned_data.get('renovation', '')
                details.furnishing = form.cleaned_data.get('furnishing', '')
                details.appliances = form.cleaned_data.get('appliances', [])
                details.multimedia = form.cleaned_data.get('multimedia', [])
                details.comfort = form.cleaned_data.get('comfort', [])
                details.communications = form.cleaned_data.get('communications', [])
                details.infrastructure = form.cleaned_data.get('infrastructure', [])
                details.landscape = form.cleaned_data.get('landscape', [])
                try:
                    details.full_clean()
                    details.save()
                except ValidationError as e:
                    messages.error(request, f"Помилка у деталях квартири: {e}")
                    return render(request, 'announcements/edit_announcement.html', {
                        'form': form,
                        'announcement': announcement,
                    })
            messages.success(request, "Оголошення успішно оновлено!")
            return redirect('announcements:announcement-detail', pk=pk)
        else:
            messages.error(request, "Помилка у формі. Перевірте введені дані.")
    else:
        initial = {}
        if hasattr(announcement, 'apartment_details'):
            details = announcement.apartment_details
            initial.update({
                'seller_type': details.seller_type,
                'building_type': details.building_type,
                'residential_complex': details.residential_complex,
                'floor': details.floor,
                'total_area': details.total_area,
                'kitchen_area': details.kitchen_area,
                'wall_type': details.wall_type,
                'housing_type': details.housing_type,
                'rooms': details.rooms,
                'layout': details.layout,
                'bathroom': details.bathroom,
                'heating': details.heating,
                'renovation': details.renovation,
                'furnishing': details.furnishing,
                'appliances': details.appliances,
                'multimedia': details.multimedia,
                'comfort': details.comfort,
                'communications': details.communications,
                'infrastructure': details.infrastructure,
                'landscape': details.landscape,
            })
        form = AnnouncementForm(instance=announcement, initial=initial)
    return render(request, 'announcements/edit_announcement.html', {
        'form': form,
        'announcement': announcement,
    })

@login_required
def delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.user != announcement.owner:
        return JsonResponse({'status': 'error', 'error': 'Ви не маєте права видаляти це оголошення.'}, status=403)

    if request.method == "POST":
        announcement.delete()
        messages.success(request, "Оголошення успішно видалено!")
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'error': 'Невірний метод запиту.'}, status=405)

@login_required
def add_review(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    if request.user == announcement.owner:
        messages.error(request, "Ви не можете залишити відгук на власне оголошення.")
        return redirect('announcements:announcement-detail', pk=announcement.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST, user=request.user, announcement=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Відгук успішно додано!")
        else:
            messages.error(request, "Помилка у формі відгуку. Перевірте введені дані.")
    return redirect('announcements:announcement-detail', pk=announcement.id)

def get_subcategories(request, category_id):
    # Fetch subcategories if Category model supports parent_id
    try:
        category = Category.objects.get(id=category_id)
        subcategories = Category.objects.filter(parent=category).values('id', 'name')
        return JsonResponse(list(subcategories), safe=False)
    except Category.DoesNotExist:
        return JsonResponse([], safe=False)