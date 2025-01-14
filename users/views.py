from django.shortcuts import render
from .forms import CustomSignupForm


def signup_view(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('account_login')  # Redirect to login after successful registration
    else:
        form = CustomSignupForm()
    return render(request, 'account/signup.html', {'form': form})

def login_view(request):
    return render(request, 'account/login.html')  # Шлях до login.html