from django import forms
from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm
class CustomSignupForm(UserCreationForm):
    email = forms.EmailField(label='Електронна пошта', max_length=254, required=True)
    phone = forms.CharField(max_length=15, required=False, label='Телефон')
    profile_picture = forms.ImageField(required=False, label='Фото профілю')
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label='Дата народження')
    address = forms.CharField(max_length=255, required=False, label='Адреса')

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'birth_date', 'address', 'profile_picture', 'password1', 'password2']