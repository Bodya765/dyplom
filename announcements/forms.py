from django import forms
from .models import Announcement, Review, Category
from allauth.account.forms import SignupForm
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User



class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='Імʼя', widget=forms.TextInput(attrs={'placeholder': 'Введіть ваше імʼя', 'aria-label': 'Ваше імʼя'}))

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
        # Set announcement and user if available
        review.announcement = self.cleaned_data.get('announcement')
        review.user = self.cleaned_data.get('user')
        if commit:
            review.save()
        return review

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'description', 'price', 'location', 'category', 'image', 'city', 'region']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Введіть заголовок', 'aria-label': 'Заголовок оголошення'}),
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Опис оголошення', 'aria-label': 'Опис'}),
            'price': forms.NumberInput(attrs={'placeholder': 'Вкажіть ціну', 'aria-label': 'Ціна'}),
            'location': forms.TextInput(attrs={'placeholder': 'Місцезнаходження', 'aria-label': 'Місцезнаходження'}),
            'city': forms.TextInput(attrs={'placeholder': 'Місто', 'aria-label': 'Місто'}),
            'region': forms.TextInput(attrs={'placeholder': 'Область', 'aria-label': 'Область'}),
            'category': forms.Select(attrs={'aria-label': 'Категорія'})  # Вибір категорії
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Додаємо список категорій до поля 'category'
        self.fields['category'].queryset = Category.objects.all()

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and not image.name.endswith(('jpg', 'jpeg', 'png')):
            raise forms.ValidationError("Дозволено завантажувати лише зображення формату jpg, jpeg або png.")
        return image


class ProfileForm(UserChangeForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)  # Password is optional
    profile_picture = forms.ImageField(required=False)  # Field for uploading profile photo

    class Meta:
        model = User
        fields = ['username', 'password', 'profile_picture']