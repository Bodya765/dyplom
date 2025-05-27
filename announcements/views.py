import requests
import json
import unicodedata
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.db.models import Q
from .models import Announcement, Category, ApartmentDetails, Review, Location, SupportRequest,Notification
from .forms import AnnouncementForm, ProfileForm, ReviewForm, UserProfileForm
import random
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError
from .utils import notify_user_rejection
logger = logging.getLogger(__name__)


def paginate_queryset(queryset, request, per_page=10):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
        logger.info(
            f"Пагінація: Сторінка {page_number}, Об’єктів: {page_obj.object_list.count()}, Заголовки: {[a.title for a in page_obj.object_list]}")
        return page_obj
    except PageNotAnInteger:
        logger.warning(f"Пагінація: Некоректний номер сторінки '{page_number}', повертаємо сторінку 1")
        return paginator.page(1)
    except EmptyPage:
        logger.warning(f"Пагінація: Сторінка {page_number} порожня, повертаємо останню сторінку")
        return paginator.page(paginator.num_pages)


def is_admin(user):
    return user.is_authenticated and user.is_superuser


def profile(request):
    return render(request, 'announcements/profile.html')


def home(request):
    recent_ids = request.session.get('recent_announcements', [])
    try:
        recent_ids = [int(id) for id in recent_ids]
        recent_announcements = Announcement.objects.filter(id__in=recent_ids, status='approved').select_related(
            'category', 'owner')[:5]
    except (ValueError, TypeError):
        recent_announcements = []
    return render(request, 'announcements/home.html', {
        'recent_announcements': recent_announcements,
    })


def announcement_autocomplete(request):
    query = request.GET.get('query', '').strip()
    logger.info(f"Автодоповнення: Запит '{query}'")
    if len(query) < 2:
        logger.info("Автодоповнення: Запит занадто короткий (< 2 символи)")
        return JsonResponse([], safe=False)

    try:
        suggestions = Announcement.objects.filter(
            status='approved',
            title__icontains=query
        ).values_list('title', flat=True).distinct()[:10]
        suggestions_list = list(suggestions)
        logger.info(f"Автодоповнення: Знайдено {len(suggestions_list)} пропозицій: {suggestions_list}")
        if not suggestions_list and query.lower() == 'test':
            suggestions_list = ['Тестове оголошення 1', 'Тестове оголошення 2']
            logger.info("Автодоповнення: Тестовий режим активовано")
        return JsonResponse(suggestions_list, safe=False)
    except Exception as e:
        logger.error(f"Автодоповнення: Помилка: {str(e)}")
        return JsonResponse([], safe=False)


def search_results(request):
    logger.info("Виконується search_results версія 2025-05-23 v5")
    search_query = request.GET.get('search', '').strip()
    search_query = unicodedata.normalize('NFKC', search_query)
    logger.info(f"Пошук: Запит '{search_query}' (довжина: {len(search_query)}, репрезентація: {repr(search_query)})")

    try:
        raw_query = request.GET.get('search', '')
        logger.info(f"Необроблений запит: '{raw_query}', репрезентація: {repr(raw_query)}")
        announcements = Announcement.objects.filter(status='approved').select_related('category', 'owner')
        logger.info(f"Початкових оголошень (status='approved'): {announcements.count()}")
        if search_query:
            title_filter = Q(title__icontains=search_query) & Q(title__isnull=False)
            announcements = announcements.filter(title_filter)
            logger.info(f"Фільтрація за: title__icontains='{search_query}'")
            count = announcements.count()
            logger.info(f"Знайдено оголошень до пагінації: {count}")
            if count > 0:
                titles = list(announcements.values_list('title', flat=True))
                logger.info(f"Заголовки: {titles}")
            else:
                logger.warning(f"Не знайдено оголошень за запитом '{search_query}'")
                all_titles = list(Announcement.objects.filter(status='approved').values_list('title', flat=True))
                logger.info(f"Усі заголовки в базі: {all_titles}")
        logger.info(f"Тип announcements: {type(announcements)}")
        page_obj = paginate_queryset(announcements, request)
        logger.info(f"Пошук: Об’єктів на сторінці: {page_obj.object_list.count()}, заголовки: {[a.title for a in page_obj.object_list]}")
        logger.info(f"Параметр сторінки: {request.GET.get('page', '1')}")
        return render(request, 'announcements/search_results.html', {
            'announcements': page_obj,
            'search_query': search_query,
        })
    except Exception as e:
        logger.error(f"Пошук: Помилка: {str(e)}")
        return render(request, 'announcements/search_results.html', {
            'announcements': [],
            'search_query': search_query,
            'error': "Помилка пошуку. Спробуйте ще раз."
        })


def announcement_detail(request, pk):
    announcement = get_object_or_404(
        Announcement.objects.select_related('category', 'owner').prefetch_related('reviews').filter(status='approved'),
        pk=pk
    )
    reviews = announcement.reviews.all()
    review_form = ReviewForm(user=request.user, announcement=announcement) if request.user.is_authenticated else None

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
            announcement.status = 'pending'
            announcement.save()

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
                    messages.error(request, f"Помилка в деталях квартири: {e}")
                    return render(request, 'announcements/create_announcement.html', {
                        'form': form,
                        'categories': Category.objects.all(),
                    })

            messages.success(request, "Оголошення створено та відправлено на модерацію!")
            return redirect('announcements:profile_edit')
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
    announcements = Announcement.objects.filter(category=category, status='approved').select_related('owner')

    sort_by = request.GET.get('sort_by', '')
    price_from = request.GET.get('price_from')
    price_to = request.GET.get('price_to')

    if sort_by == 'oldest':
        announcements = announcements.order_by('created_at')
    elif sort_by == 'newest':
        announcements = announcements.order_by('-created_at')

    if price_from:
        announcements = announcements.filter(price__gte=price_from)
    if price_to:
        announcements = announcements.filter(price__lte=price_to)

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
    announcements = Announcement.objects.filter(category=category, status='approved').select_related('owner')
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


def location_api(request):
    query = request.GET.get('search', '')
    random_results = request.GET.get('random', '')
    if random_results:
        locations = Location.objects.all()
        if locations.exists():
            locations = random.sample(list(locations), min(int(random_results), locations.count()))
        else:
            locations = []
    else:
        locations = Location.objects.filter(
            Q(name__icontains=query) | Q(district__icontains=query)
        )[:10]
    results = [
        {
            'name': location.name,
            'district': location.district if location.district else ''
        }
        for location in locations
    ]
    return JsonResponse(results, safe=False)


@login_required
def profile_edit(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
    else:
        profile_form = UserProfileForm(instance=profile)
    announcements = Announcement.objects.filter(owner=request.user).order_by('-created_at')
    paginator = Paginator(announcements, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'announcements/profile_edit.html', {
        'profile_form': profile_form,
        'announcements': page_obj,
        'page_obj': page_obj,
    })


@login_required
def update_profile(request):
    if request.method == "POST":
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        if username and username != request.user.username:
            request.user.username = username
            request.user.save()
        request.user.profile.phone = phone
        request.user.profile.save()
        request.user.email = email
        request.user.save()
        return JsonResponse({
            'success': True,
            'username': username or request.user.username,
            'phone': phone,
            'email': email,
        })
    return JsonResponse({'success': False, 'error': 'Невірний метод запиту'})


@login_required
def update_avatar(request):
    if request.method == "POST" and request.FILES.get('avatar'):
        avatar = request.FILES['avatar']
        request.user.profile.avatar = avatar
        request.user.profile.save()
        return JsonResponse({'success': True, 'avatar_url': request.user.profile.avatar.url})
    return JsonResponse({'success': False, 'error': 'Файл не завантажено'})


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
            announcement.status = 'pending'
            announcement.save()
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
            messages.success(request, "Оголошення оновлено та відправлено на модерацію!")
            return redirect('home')
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
def notifications(request):
    # Отримуємо всі сповіщення користувача
    user_notifications = Notification.objects.filter(user=request.user)
    # Оновлюємо статус прочитання для непрочитаних
    user_notifications.filter(is_read=False).update(is_read=True)
    context = {'notifications': user_notifications}
    return render(request, 'announcements/notifications.html', context)
@login_required
def add_review(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    if request.user == announcement.owner:
        messages.error(request, "Ви не можете залишити відгук на власне оголошення.")
        return redirect('announcements:announcement_detail', pk=announcement.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST, user=request.user, announcement=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Відгук успішно додано!")
        else:
            messages.error(request, "Помилка у формі відгуку. Перевірте введені дані.")
    return redirect('announcements:announcement_detail', pk=announcement.id)


def get_subcategories(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
        subcategories = Category.objects.filter(parent=category).values('id', 'name')
        return JsonResponse(list(subcategories), safe=False)
    except Category.DoesNotExist:
        return JsonResponse([], safe=False)


@user_passes_test(is_admin)
def admin_panel(request):
    pending_announcements = Announcement.objects.filter(status='pending').select_related('owner', 'category').order_by('-created_at')
    logger.debug(f"Number of pending announcements: {pending_announcements.count()}")

    if request.method == 'POST':
        pk = request.POST.get('announcement_id')
        action = request.POST.get('action')
        announcement = Announcement.objects.get(pk=pk)

        if action == 'approve':
            announcement.status = 'approved'
            announcement.save()
            messages.success(request, f"Оголошення '{announcement.title}' схвалено.")
            logger.info(f"Announcement #{pk} approved")
        elif action == 'reject':
            admin_comment = request.POST.get('admin_comment', 'Не вказано причину')
            announcement.status = 'rejected'
            announcement.admin_comment = admin_comment
            announcement.save()
            try:
                notify_user_rejection(announcement)
                messages.success(request, f"Оголошення '{announcement.title}' відхилено. Користувачу надіслано сповіщення.")
                logger.info(f"Announcement #{pk} rejected, notification sent")
            except Exception as e:
                logger.error(f"Error sending notification for announcement #{pk}: {str(e)}")
                messages.error(request, f"Помилка при відправці сповіщення: {str(e)}")

        return redirect('announcements:admin_panel')

    page_obj = paginate_queryset(pending_announcements, request, per_page=10)
    return render(request, 'announcements/admin_panel.html', {
        'announcements': page_obj,
    })


@user_passes_test(is_admin)
def moderate_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            announcement.status = 'approved'
            messages.success(request, f"Оголошення '{announcement.title}' схвалено.")
        elif action == 'reject':
            announcement.status = 'rejected'
            messages.success(request, f"Оголошення '{announcement.title}' відхилено.")
        announcement.save()
        return redirect('announcements:admin_panel')
    return render(request, 'announcements/moderate_announcement.html', {
        'announcement': announcement,
    })


@require_GET
def get_requests(request):
    requests = SupportRequest.objects.filter(status="pending", response__isnull=True).order_by('-created_at')
    data = [{
        'id': req.id,
        'user_id': req.user_id,
        'username': req.username,
        'question': req.question,
        'response': req.response,
        'status': 'Очікує',
        'handled_by_admin': req.handled_by_admin
    } for req in requests]
    return JsonResponse(data, safe=False)


@require_POST
@csrf_exempt
def update_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_id = data.get('id')
            response_text = data.get('response')

            req = SupportRequest.objects.get(id=request_id)
            req.response = response_text
            req.status = 'answered'
            req.handled_by_admin = False
            req.save()
            return JsonResponse({'status': 'success'})
        except SupportRequest.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Запит не знайдено'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Невірний метод'}, status=400)

