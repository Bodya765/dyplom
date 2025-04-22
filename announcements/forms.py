# forms.py
from django import forms
from .models import Announcement, Review, Category, Location
from allauth.account.forms import SignupForm
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='Імʼя', widget=forms.TextInput(
        attrs={'placeholder': 'Введіть ваше імʼя', 'aria-label': 'Ваше імʼя'}))

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError("Імʼя не може бути порожнім.")
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
            'rating': forms.Select(choices=[(i, f"{i} зірок") for i in range(1, 6)], attrs={'aria-label': 'Оцінка'}),
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Напишіть ваш відгук...'}),
        }

    def save(self, commit=True):
        review = super().save(commit=False)
        review.announcement = self.cleaned_data.get('announcement')
        review.user = self.cleaned_data.get('user')
        if commit:
            review.save()
        return review


class AnnouncementForm(forms.ModelForm):
    location = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'aria-label': 'Місцезнаходження',
            'class': 'form-control',
            'id': 'location',
            'placeholder': 'Введіть місто'
        })
    )
    subcategory = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'subcategory'})
    )
    deal_type = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'deal_type'})
    )

    class Meta:
        model = Announcement
        fields = ['title', 'description', 'price', 'location', 'category', 'subcategory', 'deal_type', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Введіть заголовок', 'aria-label': 'Заголовок оголошення'}),
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Опис оголошення', 'aria-label': 'Опис'}),
            'price': forms.NumberInput(attrs={'placeholder': 'Вкажіть ціну', 'aria-label': 'Ціна'}),
            'category': forms.Select(attrs={'aria-label': 'Категорія', 'id': 'id_category'}),
            'image': forms.ClearableFileInput(attrs={'aria-label': 'Зображення оголошення'}),
        }

    def clean_location(self):
        location_name = self.cleaned_data.get('location')
        if not location_name:
            raise forms.ValidationError("Місцезнаходження не може бути порожнім.")

        # Розділяємо введений рядок на місто та район (наприклад, "Київ, Шевченківський")
        try:
            parts = location_name.split(',', 1)
            name = parts[0].strip()
            district = parts[1].strip() if len(parts) > 1 else ''
        except IndexError:
            name = location_name.strip()
            district = ''

        # Шукаємо або створюємо об’єкт Location
        location, created = Location.objects.get_or_create(
            name=name,
            district=district,
            defaults={'city': None}  # Якщо потрібен зв’язок із City, його можна додати
        )
        return location

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and not image.name.lower().endswith(('jpg', 'jpeg', 'png')):
            raise forms.ValidationError("Дозволено завантажувати лише зображення формату jpg, jpeg або png.")
        return image

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Ціна має бути більшою за 0.")
        return price

    def clean_subcategory(self):
        subcategory = self.cleaned_data.get('subcategory')
        if not subcategory:
            return
        return subcategory

    def clean_deal_type(self):
        deal_type = self.cleaned_data.get('deal_type')
        if not deal_type:
            return
        return deal_type


class ProfileForm(UserChangeForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'profile_picture']

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 8:
            raise forms.ValidationError("Пароль має бути не менше 8 символів.")
        return password