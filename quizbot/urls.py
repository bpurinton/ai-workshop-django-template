from django.urls import path
from . import views

app_name = 'quizbot'

urlpatterns = [
    path('', views.home, name='home'),
    path('topic/create/', views.create_topic, name='create_topic'),
    path('quiz/start/<int:topic_id>/', views.start_quiz, name='start_quiz'),
    path('quiz/<int:quiz_id>/question/', views.get_question, name='get_question'),
    path('quiz/<int:quiz_id>/results/', views.quiz_results, name='quiz_results'),
]
