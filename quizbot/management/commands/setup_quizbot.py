from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from quizbot.models import Topic

class Command(BaseCommand):
    help = 'Setup initial users and topics for QuizBot'

    def handle(self, *args, **kwargs):
        # Create sample users
        users = ['alice', 'bob']
        password = 'quizbot123'
        
        for username in users:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(username=username, password=password)
                self.stdout.write(self.style.SUCCESS(f'Successfully created user: {username}'))
            else:
                self.stdout.write(self.style.WARNING(f'User {username} already exists'))

        # Create some initial topics
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()

        topics = ['Python Programming', 'World History', 'Science Fiction Movies']
        for topic_name in topics:
            if not Topic.objects.filter(name=topic_name).exists():
                Topic.objects.create(name=topic_name, creator=admin_user)
                self.stdout.write(self.style.SUCCESS(f'Successfully created topic: {topic_name}'))
