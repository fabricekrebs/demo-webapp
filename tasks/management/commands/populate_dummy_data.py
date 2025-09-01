import secrets
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from tasks.models import Project, Task


class Command(BaseCommand):
    help = "Populate the database with dummy users, projects, and random tasks"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=50, help="Number of tasks to create (default: 50)")

    def handle(self, *args, **kwargs):
        count = kwargs["count"]
        Task.objects.all().delete()  # Clear existing tasks
        Project.objects.all().delete()  # Clear existing projects
        User.objects.exclude(is_superuser=True).delete()  # Clear non-superusers

        # Create 5 dummy users
        user_names = ["alice", "bob", "charlie", "david", "eve"]
        users = []
        for name in user_names:
            user, _ = User.objects.get_or_create(username=name, defaults={"email": f"{name}@example.com"})
            users.append(user)

        # Create 5 dummy projects
        project_names = [
            ("Apollo", "Space mission project."),
            ("Mercury", "First human spaceflight program."),
            ("Gemini", "Two-person spacecraft project."),
            ("Artemis", "Return to the Moon."),
            ("Voyager", "Interstellar mission."),
        ]
        projects = []
        for name, desc in project_names:
            project, _ = Project.objects.get_or_create(name=name, defaults={"description": desc})
            projects.append(project)

        title_parts = [
            "Complete",
            "Fix",
            "Prepare",
            "Write",
            "Update",
            "Review",
            "Design",
            "Refactor",
            "Optimize",
            "Conduct",
            "Deploy",
            "Backup",
            "Research",
            "Attend",
            "Plan",
        ]
        title_objects = [
            "project report",
            "bugs in the code",
            "presentation",
            "unit tests",
            "documentation",
            "pull requests",
            "new feature",
            "codebase",
            "database queries",
            "user testing",
            "to production",
            "database",
            "new technologies",
            "team meeting",
            "sprint tasks",
        ]

        description_parts = [
            "This task involves",
            "Fix all the",
            "Prepare a",
            "Write",
            "Update the",
            "Review the",
            "Design a",
            "Refactor the",
            "Optimize the",
            "Conduct",
            "Deploy the",
            "Backup the",
            "Research",
            "Attend the",
            "Plan the",
        ]
        description_objects = [
            "project report by the end of the week.",
            "bugs reported in the issue tracker.",
            "presentation for the upcoming client meeting.",
            "unit tests for the new features added.",
            "project documentation with the latest changes.",
            "pull requests submitted by the team members.",
            "new feature based on the client requirements.",
            "existing codebase to improve readability.",
            "database queries to enhance performance.",
            "user testing to gather feedback on the new feature.",
            "latest version of the application to production.",
            "database before making any changes.",
            "new technologies that can be used in the project.",
            "team meeting to discuss the project progress.",
            "tasks for the upcoming sprint.",
        ]

        priorities = [1, 2, 3, 4]

        for _ in range(count):
            title = f"{secrets.choice(title_parts)} {secrets.choice(title_objects)}"  # nosec B311
            description = f"{secrets.choice(description_parts)} {secrets.choice(description_objects)}"  # nosec B311
            owner = secrets.choice(users)
            project = secrets.choice(projects)
            creation_date = timezone.now() - timedelta(days=secrets.randbelow(31))
            due_date = creation_date + timedelta(days=secrets.randbelow(30) + 1)
            duration = timedelta(hours=secrets.randbelow(8) + 1)
            priority = secrets.choice(priorities)

            Task.objects.create(
                title=title,
                description=description,
                owner=owner,
                project=project,
                creation_date=creation_date,
                due_date=due_date,
                duration=duration,
                priority=priority,
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully populated the database with {count} tasks, 5 users, and 5 projects")
        )
