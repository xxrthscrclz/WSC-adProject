from django.shortcuts import render

from rooms.models import StudyRoom


def home(request):
    rooms = StudyRoom.objects.filter(is_active=True)[:3]
    return render(request, "home.html", {"rooms": rooms})
