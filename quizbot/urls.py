from django.urls import path

from . import views

app_name = "quizbot"

urlpatterns = [
    path("", views.home, name="home"),
    path("start/", views.start_quiz, name="start"),
    path("<int:quiz_id>/", views.play, name="play"),
    path("<int:quiz_id>/answer/", views.answer, name="answer"),
    path("<int:quiz_id>/results/", views.results, name="results"),
]
