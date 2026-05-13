from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Topic, Quiz, Question
from .ai import generate_question, evaluate_answer

@login_required
def home(request):
    topics = Topic.objects.all()
    return render(request, 'quizbot/home.html', {'topics': topics})

@login_required
def create_topic(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Topic.objects.create(name=name, creator=request.user)
            return redirect('quizbot:home')
    return render(request, 'quizbot/create_topic.html')

@login_required
def start_quiz(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    quiz = Quiz.objects.create(topic=topic, user=request.user)
    return redirect('quizbot:get_question', quiz_id=quiz.id)

@login_required
def get_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    
    if quiz.completed:
        return redirect('quizbot:quiz_results', quiz_id=quiz.id)
    
    # Check if there's an unanswered question
    current_question = quiz.questions.filter(user_answer__isnull=True).first()
    
    if not current_question:
        # Check if we should generate a new one
        total_questions = quiz.questions.count()
        if total_questions >= 5:
            quiz.completed = True
            quiz.save()
            return redirect('quizbot:quiz_results', quiz_id=quiz.id)
        
        # Determine difficulty based on progress
        # "increasing difficulty as they get each question correct"
        difficulty = quiz.current_difficulty
        if difficulty > 5: difficulty = 5
        
        ai_data = generate_question(quiz.topic.name, difficulty)
        current_question = Question.objects.create(
            quiz=quiz,
            text=ai_data['question'],
            options=ai_data['options'],
            correct_answer=ai_data['answer'],
            difficulty=difficulty
        )

    if request.method == 'POST':
        user_answer = request.POST.get('answer')
        current_question.user_answer = user_answer
        is_correct = evaluate_answer(current_question.correct_answer, user_answer)
        current_question.is_correct = is_correct
        current_question.save()
        
        if is_correct:
            quiz.score += 1
            quiz.save()
        
        # Check if 5 questions reached
        if quiz.questions.count() >= 5:
            quiz.completed = True
            quiz.save()
            return redirect('quizbot:quiz_results', quiz_id=quiz.id)
        
        return redirect('quizbot:get_question', quiz_id=quiz.id)

    return render(request, 'quizbot/question.html', {
        'quiz': quiz,
        'question': current_question,
        'progress': quiz.questions.count()
    })

@login_required
def quiz_results(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    
    # Calculate proficiency
    proficiency = "Beginner"
    if quiz.score == 5: proficiency = "Expert"
    elif quiz.score >= 3: proficiency = "Intermediate"
    
    return render(request, 'quizbot/results.html', {
        'quiz': quiz,
        'proficiency': proficiency
    })
