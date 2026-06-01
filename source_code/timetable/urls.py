from django.urls import path

from . import views

app_name = "timetable"

urlpatterns = [
    path("", views.schedule_list, name="list"),
    path("add/", views.schedule_add, name="add"),
    path("recommend/", views.study_recommend, name="recommend"),
    path("<int:schedule_id>/delete/", views.schedule_delete, name="delete"),
]
