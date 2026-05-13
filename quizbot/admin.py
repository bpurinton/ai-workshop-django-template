from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    readonly_fields = (
        "order",
        "difficulty",
        "text",
        "correct_answer",
        "user_answer",
        "is_correct",
    )


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "topic", "created_at", "completed_at", "score")
    list_filter = ("user",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "quiz",
        "order",
        "difficulty",
        "correct_answer",
        "user_answer",
        "is_correct",
    )
    list_filter = ("difficulty", "is_correct")
