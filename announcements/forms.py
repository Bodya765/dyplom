from django import forms
from .models import Announcement, Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} зірок") for i in range(1, 6)]),
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Напишіть ваш відгук...'}),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'description', 'price', 'location', 'category', 'image', 'city', 'region']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Введіть заголовок'}),
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Опис оголошення'}),
            'price': forms.NumberInput(attrs={'placeholder': 'Вкажіть ціну'}),
            'location': forms.TextInput(attrs={'placeholder': 'Місцезнаходження'}),
            'city': forms.TextInput(attrs={'placeholder': 'Місто'}),
            'region': forms.TextInput(attrs={'placeholder': 'Область'}),
        }
