from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from quizbot.models import Question, Quiz
from quizbot.services import (
    QuestionGenerationError,
    _stub_question,
    _validate_payload,
    generate_question,
)

User = get_user_model()


def fake_question(topic, difficulty, previous_questions=None):
    """A deterministic fake `generate_question` for tests.

    Correct answer is "A" on odd difficulties, "B" on even ones — gives us
    a predictable mix of right/wrong outcomes when the user always answers "A".
    """
    correct = "A" if difficulty % 2 == 1 else "B"
    return {
        "text": f"Mock question about {topic} at difficulty {difficulty}",
        "choices": {"A": "alpha", "B": "beta", "C": "gamma", "D": "delta"},
        "correct_answer": correct,
        "explanation": "Mocked explanation.",
    }


class FixtureUsersTests(TestCase):
    fixtures = ["sample_users.json"]

    def test_sample_users_can_sign_in(self):
        for username in ["alice", "bob", "carol"]:
            ok = self.client.login(username=username, password="quizbot123")
            self.assertTrue(ok, f"{username} should be able to sign in with quizbot123")
            self.client.logout()


class AuthGatingTests(TestCase):
    fixtures = ["sample_users.json"]

    def test_home_redirects_anonymous_to_login(self):
        response = self.client.get(reverse("quizbot:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_root_redirects_to_quizbot_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("quizbot:home"), response["Location"])


class StubServiceTests(TestCase):
    @override_settings(OPENAI_API_KEY="")
    def test_generate_question_uses_stub_when_no_api_key(self):
        result = generate_question("Photosynthesis", 1)
        self.assertEqual(result["correct_answer"], "A")
        self.assertEqual(set(result["choices"].keys()), {"A", "B", "C", "D"})
        self.assertIn("Photosynthesis", result["text"])

    def test_validate_payload_rejects_bad_choices(self):
        with self.assertRaises(QuestionGenerationError):
            _validate_payload(
                {
                    "question": "?",
                    "choices": {"A": "x", "B": "y"},
                    "correct": "A",
                }
            )

    def test_validate_payload_rejects_bad_correct_letter(self):
        with self.assertRaises(QuestionGenerationError):
            _validate_payload(
                {
                    "question": "?",
                    "choices": {"A": "x", "B": "y", "C": "z", "D": "w"},
                    "correct": "Z",
                }
            )

    def test_stub_increments_question_number(self):
        first = _stub_question("T", 1, [])
        second = _stub_question("T", 2, ["q1"])
        self.assertIn("#1", first["text"])
        self.assertIn("#2", second["text"])


@patch("quizbot.views.generate_question", side_effect=fake_question)
class QuizFlowTests(TestCase):
    fixtures = ["sample_users.json"]

    def setUp(self):
        self.client.login(username="alice", password="quizbot123")

    def test_start_quiz_creates_quiz_and_first_question(self, _mock_gen):
        response = self.client.post(
            reverse("quizbot:start"), {"topic": "The Roman Empire"}
        )
        self.assertEqual(response.status_code, 302)
        quiz = Quiz.objects.get()
        self.assertEqual(quiz.topic, "The Roman Empire")
        self.assertEqual(quiz.user.username, "alice")
        self.assertEqual(quiz.questions.count(), 1)
        first = quiz.questions.get()
        self.assertEqual(first.order, 1)
        self.assertEqual(first.difficulty, 1)

    def test_start_quiz_rejects_blank_topic(self, _mock_gen):
        response = self.client.post(reverse("quizbot:start"), {"topic": " "})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Quiz.objects.count(), 0)

    def test_start_quiz_rejects_get(self, _mock_gen):
        response = self.client.get(reverse("quizbot:start"))
        self.assertEqual(response.status_code, 405)

    def test_full_flow_perfect_score(self, _mock_gen):
        self.client.post(reverse("quizbot:start"), {"topic": "Trees"})
        quiz = Quiz.objects.get()
        for _ in range(Quiz.NUM_QUESTIONS):
            q = quiz.next_unanswered()
            self.assertIsNotNone(q)
            self.client.post(
                reverse("quizbot:answer", args=[quiz.id]),
                {"answer": q.correct_answer},
            )
        quiz.refresh_from_db()
        self.assertTrue(quiz.is_complete)
        self.assertEqual(quiz.score, 5)
        self.assertEqual(quiz.proficiency, "Expert")
        self.assertEqual(quiz.questions.count(), 5)
        difficulties = list(quiz.questions.values_list("difficulty", flat=True))
        self.assertEqual(difficulties, [1, 2, 3, 4, 5])

    def test_full_flow_mixed_score(self, _mock_gen):
        """Always answer A. fake_question has correct=A on odd difficulties."""
        self.client.post(reverse("quizbot:start"), {"topic": "Math"})
        quiz = Quiz.objects.get()
        for _ in range(Quiz.NUM_QUESTIONS):
            self.client.post(reverse("quizbot:answer", args=[quiz.id]), {"answer": "A"})
        quiz.refresh_from_db()
        self.assertEqual(quiz.score, 3)  # difficulties 1,3,5 correct
        self.assertEqual(quiz.proficiency, "Intermediate")

    def test_invalid_letter_returns_400(self, _mock_gen):
        self.client.post(reverse("quizbot:start"), {"topic": "Birds"})
        quiz = Quiz.objects.get()
        response = self.client.post(
            reverse("quizbot:answer", args=[quiz.id]), {"answer": "Z"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(quiz.questions.filter(user_answer="").count(), 1)

    def test_cannot_access_another_users_quiz(self, _mock_gen):
        self.client.post(reverse("quizbot:start"), {"topic": "Birds"})
        quiz = Quiz.objects.get()
        self.client.logout()
        self.client.login(username="bob", password="quizbot123")
        response = self.client.get(reverse("quizbot:play", args=[quiz.id]))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(
            reverse("quizbot:answer", args=[quiz.id]), {"answer": "A"}
        )
        self.assertEqual(response.status_code, 404)

    def test_results_page_renders_score(self, _mock_gen):
        self.client.post(reverse("quizbot:start"), {"topic": "Anything"})
        quiz = Quiz.objects.get()
        for _ in range(Quiz.NUM_QUESTIONS):
            q = quiz.next_unanswered()
            self.client.post(
                reverse("quizbot:answer", args=[quiz.id]),
                {"answer": q.correct_answer},
            )
        response = self.client.get(reverse("quizbot:results", args=[quiz.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "5 / 5")
        self.assertContains(response, "Expert")

    def test_play_redirects_to_results_when_complete(self, _mock_gen):
        self.client.post(reverse("quizbot:start"), {"topic": "Anything"})
        quiz = Quiz.objects.get()
        for _ in range(Quiz.NUM_QUESTIONS):
            q = quiz.next_unanswered()
            self.client.post(
                reverse("quizbot:answer", args=[quiz.id]),
                {"answer": q.correct_answer},
            )
        response = self.client.get(reverse("quizbot:play", args=[quiz.id]))
        self.assertRedirects(response, reverse("quizbot:results", args=[quiz.id]))
