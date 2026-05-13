from django.conf import settings
from django.db import models


class Quiz(models.Model):
    NUM_QUESTIONS = 5

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quizzes"
    )
    topic = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.topic}"

    @property
    def is_complete(self):
        return self.completed_at is not None

    @property
    def score(self):
        return self.questions.filter(is_correct=True).count()

    @property
    def proficiency(self):
        s = self.score
        if s <= 1:
            return "Beginner"
        if s == 2:
            return "Novice"
        if s == 3:
            return "Intermediate"
        if s == 4:
            return "Advanced"
        return "Expert"

    def next_unanswered(self):
        return self.questions.filter(user_answer="").order_by("order").first()


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    order = models.PositiveSmallIntegerField()
    difficulty = models.PositiveSmallIntegerField()
    text = models.TextField()
    choices = models.JSONField()
    correct_answer = models.CharField(max_length=1)
    user_answer = models.CharField(max_length=1, blank=True, default="")
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["order"]
        unique_together = ("quiz", "order")

    def __str__(self):
        return f"Q{self.order} (d{self.difficulty}) of {self.quiz_id}"

    def record_answer(self, letter):
        letter = (letter or "").strip().upper()
        self.user_answer = letter
        self.is_correct = letter == self.correct_answer
        self.save(update_fields=["user_answer", "is_correct"])
        return self.is_correct
