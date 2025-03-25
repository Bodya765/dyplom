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

    class Meta:
        model = Announcement
        fields = ['title', 'description', 'price', 'location', 'category', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Введіть заголовок', 'aria-label': 'Заголовок оголошення'}),
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Опис оголошення', 'aria-label': 'Опис'}),
            'price': forms.NumberInput(attrs={'placeholder': 'Вкажіть ціну', 'aria-label': 'Ціна'}),
            'category': forms.Select(attrs={'aria-label': 'Категорія'}),
            'image': forms.ClearableFileInput(attrs={'aria-label': 'Зображення оголошення'}),
        }

    def clean_location(self):
        location_name = self.cleaned_data.get('location')
        if not location_name:
            raise forms.ValidationError("Місцезнаходження не може бути порожнім.")

        location, created = Location.objects.get_or_create(name=location_name)
        return location

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and not image.name.endswith(('jpg', 'jpeg', 'png')):
            raise forms.ValidationError("Дозволено завантажувати лише зображення формату jpg, jpeg або png.")
        return image

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Ціна має бути більшою за 0.")
        return price


class ProfileForm(UserChangeForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'profile_picture']

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise forms.ValidationError("Пароль не може бути порожнім.")
        return password
