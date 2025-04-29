from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from allauth.account.forms import SignupForm
from .models import Announcement, Review, Category, ApartmentDetails
import re

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30,
        label="Ім'я",
        widget=forms.TextInput(attrs={'placeholder': "Введіть ваше ім'я", 'aria-label': "Ваше ім'я"})
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

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.save()
        return user

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
    image = forms.ImageField(  # Змінено з images на image, використано ImageField
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
            'subcategory', 'deal_type', 'image'  # Додано image до fields
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

    def clean_image(self):  # Змінено з clean_images на clean_image
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

class ProfileForm(UserChangeForm):
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label="Фото профілю"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email', 'profile_picture']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('password')  # Remove password field

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            if not profile_picture.name.lower().endswith(('jpg', 'jpeg', 'png')):
                raise forms.ValidationError("Дозволено лише зображення у форматах JPG, JPEG або PNG.")
            if profile_picture.size > 2 * 1024 * 1024:  # 2MB limit
                raise forms.ValidationError("Розмір зображення не може перевищувати 2 МБ.")
        return profile_picture

    def save(self, commit=True):
        user = super().save(commit=False)
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            # Assuming a Profile model or custom storage logic is implemented
            user.profile_picture = profile_picture  # Adjust based on actual implementation
        if commit:
            user.save()
        return user