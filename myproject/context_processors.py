# myproject/context_processors.py
from django.conf import settings

def recaptcha_keys(request):
    return {
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_SITE_KEY
    }