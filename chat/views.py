from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserStatus

@login_required
def chat_room(request, room_name):
    user_statuses = UserStatus.objects.all()
    return render(request, "chat/room.html", {"room_name": room_name, "user_statuses": user_statuses})
