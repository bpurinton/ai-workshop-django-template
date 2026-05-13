from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import TopicForm
from .models import Question, Quiz
from .services import generate_question


@login_required
def home(request):
    quizzes = Quiz.objects.filter(user=request.user)
    return render(
        request,
        "quizbot/home.html",
        {"form": TopicForm(), "quizzes": quizzes},
    )


@login_required
@require_http_methods(["POST"])
def start_quiz(request):
    form = TopicForm(request.POST)
    if not form.is_valid():
        quizzes = Quiz.objects.filter(user=request.user)
        return render(
            request, "quizbot/home.html", {"form": form, "quizzes": quizzes}, status=400
        )
    quiz = Quiz.objects.create(user=request.user, topic=form.cleaned_data["topic"])
    _create_next_question(quiz)
    return redirect("quizbot:play", quiz_id=quiz.id)


@login_required
def play(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    if quiz.is_complete:
        return redirect("quizbot:results", quiz_id=quiz.id)

    question = quiz.next_unanswered()
    if question is None:
        quiz.completed_at = timezone.now()
        quiz.save(update_fields=["completed_at"])
        return redirect("quizbot:results", quiz_id=quiz.id)

    return render(
        request,
        "quizbot/question.html",
        {"quiz": quiz, "question": question, "total": Quiz.NUM_QUESTIONS},
    )


@login_required
@require_http_methods(["POST"])
def answer(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    if quiz.is_complete:
        return redirect("quizbot:results", quiz_id=quiz.id)

    question = quiz.next_unanswered()
    if question is None:
        return redirect("quizbot:results", quiz_id=quiz.id)

    letter = request.POST.get("answer", "").strip().upper()
    if letter not in {"A", "B", "C", "D"}:
        return HttpResponseBadRequest("Pick A, B, C, or D.")

    question.record_answer(letter)

    asked = quiz.questions.count()
    if asked >= Quiz.NUM_QUESTIONS:
        quiz.completed_at = timezone.now()
        quiz.save(update_fields=["completed_at"])
        return redirect("quizbot:results", quiz_id=quiz.id)

    _create_next_question(quiz)
    return redirect("quizbot:play", quiz_id=quiz.id)


@login_required
def results(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    return render(request, "quizbot/results.html", {"quiz": quiz})


def _create_next_question(quiz):
    asked = list(quiz.questions.all())
    order = len(asked) + 1
    difficulty = order
    previous_texts = [q.text for q in asked]
    payload = generate_question(quiz.topic, difficulty, previous_texts)
    return Question.objects.create(
        quiz=quiz,
        order=order,
        difficulty=difficulty,
        text=payload["text"],
        choices=payload["choices"],
        correct_answer=payload["correct_answer"],
        explanation=payload["explanation"],
    )
