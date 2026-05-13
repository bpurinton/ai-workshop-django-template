import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from quizbot.models import Topic, Quiz, Question
from unittest.mock import patch

@pytest.mark.django_db
class TestQuizBot:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username='testuser', password='password123')

    @pytest.fixture
    def authenticated_client(self, client, user):
        client.login(username='testuser', password='password123')
        return client

    def test_home_page_requires_login(self, client):
        response = client.get(reverse('quizbot:home'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_home_page_authenticated(self, authenticated_client):
        response = authenticated_client.get(reverse('quizbot:home'))
        assert response.status_code == 200

    def test_create_topic(self, authenticated_client):
        response = authenticated_client.post(reverse('quizbot:create_topic'), {'name': 'Django Testing'})
        assert response.status_code == 302
        assert Topic.objects.filter(name='Django Testing').exists()

    @patch('quizbot.views.generate_question')
    def test_quiz_flow(self, mock_gen, authenticated_client, user):
        topic = Topic.objects.create(name='Python', creator=user)
        
        # Mocking AI response
        mock_gen.return_value = {
            'question': 'What is Python?',
            'options': ['Snake', 'Language', 'Fruit', 'Car'],
            'answer': 'Language'
        }

        # Start quiz
        response = authenticated_client.get(reverse('quizbot:start_quiz', args=[topic.id]))
        assert response.status_code == 302
        quiz = Quiz.objects.get(topic=topic, user=user)
        
        # Get first question
        response = authenticated_client.get(reverse('quizbot:get_question', args=[quiz.id]))
        assert response.status_code == 200
        assert 'What is Python?' in response.content.decode()

        # Submit correct answer
        response = authenticated_client.post(reverse('quizbot:get_question', args=[quiz.id]), {'answer': 'Language'})
        assert response.status_code == 302
        quiz.refresh_from_db()
        assert quiz.score == 1
        assert quiz.questions.count() == 1

    def test_proficiency_calculation(self, authenticated_client, user):
        topic = Topic.objects.create(name='Math', creator=user)
        quiz = Quiz.objects.create(topic=topic, user=user, score=5, completed=True)
        
        response = authenticated_client.get(reverse('quizbot:quiz_results', args=[quiz.id]))
        assert response.status_code == 200
        assert 'Expert' in response.content.decode()
