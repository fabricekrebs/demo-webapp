import random
from django.core.management.base import BaseCommand
from myapp.models import Task
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Populate the database with random tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=300,
            help='Number of tasks to create (default: 300)'
        )

    def handle(self, *args, **kwargs):
        count = kwargs['count']
        Task.objects.all().delete()  # Clear existing tasks

        title_parts = [
            'Complete', 'Fix', 'Prepare', 'Write', 'Update', 'Review', 'Design', 'Refactor', 'Optimize', 'Conduct', 'Deploy', 'Backup', 'Research', 'Attend', 'Plan'
        ]
        title_objects = [
            'project report', 'bugs in the code', 'presentation', 'unit tests', 'documentation', 'pull requests', 'new feature', 'codebase', 'database queries', 'user testing', 'to production', 'database', 'new technologies', 'team meeting', 'sprint tasks'
        ]

        description_parts = [
            'This task involves', 'Fix all the', 'Prepare a', 'Write', 'Update the', 'Review the', 'Design a', 'Refactor the', 'Optimize the', 'Conduct', 'Deploy the', 'Backup the', 'Research', 'Attend the', 'Plan the'
        ]
        description_objects = [
            'project report by the end of the week.', 'bugs reported in the issue tracker.', 'presentation for the upcoming client meeting.', 'unit tests for the new features added.', 'project documentation with the latest changes.', 'pull requests submitted by the team members.', 'new feature based on the client requirements.', 'existing codebase to improve readability.', 'database queries to enhance performance.', 'user testing to gather feedback on the new feature.', 'latest version of the application to production.', 'database before making any changes.', 'new technologies that can be used in the project.', 'team meeting to discuss the project progress.', 'tasks for the upcoming sprint.'
        ]

        owners = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Hank', 'Ivy', 'Jack']

        priorities = [1, 2, 3, 4]

        for _ in range(count):
            title = f"{random.choice(title_parts)} {random.choice(title_objects)}"
            description = f"{random.choice(description_parts)} {random.choice(description_objects)}"
            owner = random.choice(owners)
            creation_date = timezone.now() - timedelta(days=random.randint(0, 30))
            due_date = creation_date + timedelta(days=random.randint(1, 30))
            duration = timedelta(hours=random.randint(1, 8))
            priority = random.choice(priorities)

            Task.objects.create(
                title=title,
                description=description,
                owner=owner,
                creation_date=creation_date,
                due_date=due_date,
                duration=duration,
                priority=priority
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully populated the database with {count} unique tasks'))