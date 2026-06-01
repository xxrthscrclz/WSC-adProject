from django.shortcuts import get_object_or_404, render

from .models import StudyRoom


def room_list(request):
    rooms = StudyRoom.objects.filter(is_active=True)
    return render(request, "rooms/list.html", {"rooms": rooms})


def room_detail(request, room_id):
    room = get_object_or_404(StudyRoom, pk=room_id, is_active=True)
    return render(request, "rooms/detail.html", {"room": room})
