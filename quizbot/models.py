from django.db import models
from django.contrib.auth.models import User

class Topic(models.Model):
    name = models.CharField(max_length=255)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Quiz(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def current_difficulty(self):
        return self.questions.filter(is_correct=True).count() + 1

    def __str__(self):
        return f"{self.user.username} - {self.topic.name}"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    options = models.JSONField(default=list)
    correct_answer = models.CharField(max_length=255)
    user_answer = models.CharField(max_length=255, blank=True, null=True)
    is_correct = models.BooleanField(null=True)
    difficulty = models.IntegerField(default=1) # 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:50]
