from django import forms
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
from django.contrib.auth.models import User
from allauth.account.forms import SignupForm
from .models import Announcement, Review, Category, ApartmentDetails, UserProfile
import re
from django.core.exceptions import ValidationError

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30,
        label="Ім'я",
        widget=forms.TextInput(attrs={'placeholder': "Введіть ваше ім'я", 'aria-label': "Ваше ім'я"})
    )
    email_or_phone = forms.CharField(
        max_length=100,
        label="Email або номер телефону",
        widget=forms.TextInput(attrs={'placeholder': "Введіть email або номер телефону", 'aria-label': "Email або номер телефону"})
    )

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name').strip()
        if not first_name:
            raise forms.ValidationError("Ім'я не може бути порожнім.")
        if len(first_name) < 2:
            raise forms.ValidationError("Ім'я має містити принаймні 2 символи.")
        if not re.match(r'^[\w\s-]+$', first_name, re.UNICODE):
            raise forms.ValidationError("Ім'я може містити лише літери, цифри, пробіли або дефіси.")
        return first_name

    def clean_email_or_phone(self):
        email_or_phone = self.cleaned_data.get('email_or_phone').strip()
        if not email_or_phone:
            raise forms.ValidationError("Email або номер телефону не може бути порожнім.")

        # Перевірка формату email
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        # Перевірка формату номера телефону (наприклад, +380123456789 або 0123456789)
        phone_regex = r'^\+?\d{10,15}$'

        is_email = bool(re.match(email_regex, email_or_phone))
        is_phone = bool(re.match(phone_regex, email_or_phone))

        if not (is_email or is_phone):
            raise forms.ValidationError("Введіть коректний email (наприклад, example@domain.com) або номер телефону (наприклад, +380123456789).")
        if is_email and is_phone:
            raise forms.ValidationError("Введіть лише один тип даних: email або номер телефону.")

        self.cleaned_data['is_email'] = is_email  # Зберігаємо, що було введено (email чи телефон)
        return email_or_phone

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        email_or_phone = self.cleaned_data['email_or_phone']
        # Генеруємо username на основі email_or_phone
        if self.cleaned_data.get('is_email'):
            user.username = email_or_phone.split('@')[0] + str(user.id)  # Наприклад, "example" з "example@domain.com"
            user.email = email_or_phone
        else:
            user.username = email_or_phone.replace('+', '') + str(user.id)  # Наприклад, "380123456789"
            user.profile.phone = email_or_phone
            user.profile.save()
        user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Email або номер телефону",
        widget=forms.TextInput(attrs={'placeholder': "Введіть email або номер телефону", 'aria-label': "Email або номер телефону"})
    )

    def clean_username(self):
        email_or_phone = self.cleaned_data.get('username').strip()
        if not email_or_phone:
            raise forms.ValidationError("Email або номер телефону не може бути порожнім.")

        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        phone_regex = r'^\+?\d{10,15}$'

        is_email = bool(re.match(email_regex, email_or_phone))
        is_phone = bool(re.match(phone_regex, email_or_phone))

        if not (is_email or is_phone):
            raise forms.ValidationError("Введіть коректний email (наприклад, example@domain.com) або номер телефону (наприклад, +380123456789).")

        # Шукаємо користувача за email або телефоном
        if is_email:
            try:
                user = User.objects.get(email=email_or_phone)
                return user.username
            except User.DoesNotExist:
                raise forms.ValidationError("Користувач з таким email не знайдений.")
        else:
            try:
                profile = UserProfile.objects.get(phone=email_or_phone)
                return profile.user.username
            except UserProfile.DoesNotExist:
                raise forms.ValidationError("Користувач з таким номером телефону не знайдений.")

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f"{i} зірок") for i in range(1, 6)],
                attrs={'aria-label': 'Оцінка', 'class': 'form-control'}
            ),
            'text': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Напишіть ваш відгук...',
                    'aria-label': 'Текст відгуку',
                    'class': 'form-control'
                }
            ),
        }

    def __init__(self, *args, user=None, announcement=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.announcement = announcement

    def clean(self):
        cleaned_data = super().clean()
        if not self.user or not self.announcement:
            raise forms.ValidationError("Користувач і оголошення повинні бути вказані.")
        if Review.objects.filter(user=self.user, announcement=self.announcement).exists():
            raise forms.ValidationError("Ви вже залишили відгук для цього оголошення.")
        if not cleaned_data.get('text').strip():
            raise forms.ValidationError("Текст відгуку не може бути порожнім.")
        return cleaned_data

    def save(self, commit=True):
        review = super().save(commit=False)
        review.user = self.user
        review.announcement = self.announcement
        if commit:
            review.save()
        return review

class AnnouncementForm(forms.ModelForm):
    image = forms.ImageField(
        widget=forms.FileInput(attrs={'aria-label': 'Зображення', 'class': 'form-control'}),
        required=False,
        label="Зображення"
    )
    subcategory = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'subcategory'}),
        label="Підкатегорія"
    )
    deal_type = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'deal_type'}),
        label="Тип угоди"
    )
    # ApartmentDetails fields
    seller_type = forms.ChoiceField(
        choices=ApartmentDetails._meta.get_field('seller_type').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Тип продавця"
    )
    building_type = forms.ChoiceField(
        choices=ApartmentDetails._meta.get_field('building_type').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Тип будинку"
    )
    residential_complex = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Назва ЖК'}),
        label="Назва ЖК"
    )
    floor = forms.IntegerField(
        min_value=1,
        max_value=100,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Поверх"
    )
    total_area = forms.FloatField(
        min_value=10,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        label="Загальна площа (м²)"
    )
    kitchen_area = forms.FloatField(
        min_value=5,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        label="Площа кухні (м²)"
    )
    wall_type = forms.ChoiceField(
        choices=ApartmentDetails._meta.get_field('wall_type').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Тип стін"
    )
    housing_type = forms.ChoiceField(
        choices=ApartmentDetails._meta.get_field('housing_type').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Тип житла"
    )
    rooms = forms.ChoiceField(
        choices=ApartmentDetails._meta.get_field('rooms').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Кількість кімнат"
    )
    layout = forms.ChoiceField(
        choices=ApartmentDetails._meta.get_field('layout').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Планування"
    )
    bathroom = forms.ChoiceField(
        choices=ApartmentDetails._meta.get_field('bathroom').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Санвузол"
    )
    heating = forms.ChoiceField(
        choices=ApartmentDetails._meta.get_field('heating').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Опалення"
    )
    renovation = forms.ChoiceField(
        choices=ApartmentDetails._meta.get_field('renovation').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Ремонт"
    )
    furnishing = forms.ChoiceField(
        choices=ApartmentDetails._meta.get_field('furnishing').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Меблювання"
    )
    appliances = forms.MultipleChoiceField(
        choices=[
            ('Холодильник', 'Холодильник'),
            ('Піч', 'Піч'),
            ('Мікрохвильовка', 'Мікрохвильовка'),
            ('Посудомийна машина', 'Посудомийна машина'),
            ('Пральна машина', 'Пральна машина')
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Побутова техніка"
    )
    multimedia = forms.MultipleChoiceField(
        choices=[
            ('Телевізор', 'Телевізор'),
            ('Wi-Fi', 'Wi-Fi'),
            ('Кабельне ТБ', 'Кабельне ТБ'),
            ('Супутникове ТБ', 'Супутникове ТБ')
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Мультимедіа"
    )
    comfort = forms.MultipleChoiceField(
        choices=[
            ('Балкон', 'Балкон'),
            ('Кондиціонер', 'Кондиціонер'),
            ('Ліфт', 'Ліфт'),
            ('Гараж', 'Гараж'),
            ('Охорона', 'Охорона'),
            ('Відеоспостереження', 'Відеоспостереження'),
            ('Конс’єрж', 'Конс’єрж'),
            ('Парковка', 'Парковка'),
            ('Тераса', 'Тераса'),
            ('Дитячий майданчик', 'Дитячий майданчик')
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Комфорт"
    )
    communications = forms.MultipleChoiceField(
        choices=[
            ('Газ', 'Газ'),
            ('Центральний водопровід', 'Центральний водопровід'),
            ('Електрика', 'Електрика'),
            ('Каналізація', 'Каналізація')
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Комунікації"
    )
    infrastructure = forms.MultipleChoiceField(
        choices=[
            ('Школа', 'Школа'),
            ('Супермаркет', 'Супермаркет'),
            ('Лікарня', 'Лікарня'),
            ('Аптека', 'Аптека'),
            ('Транспортна зупинка', 'Транспортна зупинка'),
            ('Залізнична станція', 'Залізнична станція'),
            ('Автовокзал', 'Автовокзал'),
            ('Банк,банкомат', 'Банк,банкомат'),
            ('Відділення пошти', 'Відділення пошти'),
            ('Кінотеатр,театр', 'Кінотеатр,театр')
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Інфраструктура"
    )
    landscape = forms.MultipleChoiceField(
        choices=[
            ('Парк', 'Парк'),
            ('Озеро', 'Озеро'),
            ('Річка', 'Річка'),
            ('Ліс', 'Ліс'),
            ('Пляж', 'Пляж'),
            ('Гора', 'Гора'),
            ('Сквер', 'Сквер')
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Ландшафт"
    )

    class Meta:
        model = Announcement
        fields = [
            'title', 'description', 'price', 'location', 'category',
            'subcategory', 'deal_type', 'image'
        ]
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'placeholder': 'Введіть заголовок',
                    'aria-label': 'Заголовок оголошення',
                    'class': 'form-control'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'rows': 5,
                    'placeholder': 'Опис оголошення',
                    'aria-label': 'Опис',
                    'class': 'form-control'
                }
            ),
            'price': forms.NumberInput(
                attrs={
                    'placeholder': 'Вкажіть ціну',
                    'aria-label': 'Ціна',
                    'class': 'form-control',
                    'step': '0.01'
                }
            ),
            'location': forms.TextInput(
                attrs={
                    'aria-label': 'Місцезнаходження',
                    'class': 'form-control',
                    'id': 'id_location',
                    'placeholder': 'Введіть місто або адресу'
                }
            ),
            'category': forms.Select(
                attrs={'aria-label': 'Категорія', 'class': 'form-control', 'id': 'id_category'}
            ),
        }

    def clean_location(self):
        location = self.cleaned_data.get('location').strip()
        if not location:
            raise forms.ValidationError("Місцезнаходження не може бути порожнім.")
        return location

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("Ціна не може бути від'ємною.")
        return price

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if not image.name.lower().endswith(('jpg', 'jpeg', 'png')):
                raise forms.ValidationError("Дозволено лише зображення у форматах JPG, JPEG або PNG.")
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Розмір зображення не може перевищувати 5 МБ.")
        return image

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('subcategory') == "Квартира":
            total_area = cleaned_data.get('total_area')
            kitchen_area = cleaned_data.get('kitchen_area')
            if total_area and kitchen_area and total_area < kitchen_area:
                raise forms.ValidationError("Загальна площа не може бути меншою за площу кухні.")
            if not total_area:
                raise forms.ValidationError("Для квартир необхідно вказати загальну площу.")
        return cleaned_data

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'avatar']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введіть номер телефону'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'phone': 'Телефон',
            'avatar': 'Фото профілю',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if not avatar.name.lower().endswith(('jpg', 'jpeg', 'png')):
                raise forms.ValidationError("Дозволено лише зображення у форматах JPG, JPEG або PNG.")
            if avatar.size > 2 * 1024 * 1024:  # 2MB limit
                raise forms.ValidationError("Розмір зображення не може перевищувати 2 МБ.")
        return avatar

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip()
            phone_regex = r'^\+?\d{10,15}$'
            if not re.match(phone_regex, phone):
                raise forms.ValidationError("Введіть коректний номер телефону (наприклад, +380123456789).")
        return phone

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        label="Ім'я",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name').strip()
        if not first_name:
            raise forms.ValidationError("Ім'я не може бути порожнім.")
        if len(first_name) < 2:
            raise forms.ValidationError("Ім'я має містити принаймні 2 символи.")
        if not re.match(r'^[\w\s-]+$', first_name, re.UNICODE):
            raise forms.ValidationError("Ім'я може містити лише літери, цифри, пробіли або дефіси.")
        return first_name