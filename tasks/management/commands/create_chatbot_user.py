"""
Django management command to create chatbot users.
Usage: python manage.py create_chatbot_user <username> [--password <password>] [--email <email>]
"""

import getpass

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a user for chatbot access"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username for the new user")
        parser.add_argument("--password", type=str, help="Password for the new user (if not provided, will be prompted)")
        parser.add_argument("--email", type=str, help="Email address for the user")
        parser.add_argument("--superuser", action="store_true", help="Create a superuser instead of regular user")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options.get("email", "")
        is_superuser = options["superuser"]

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists.')

        # Get password if not provided
        if not password:
            password = getpass.getpass("Password: ")
            password_confirm = getpass.getpass("Password (confirm): ")
            if password != password_confirm:
                raise CommandError("Passwords do not match.")

        try:
            # Create the user
            if is_superuser:
                user = User.objects.create_superuser(username=username, email=email, password=password)
                user_type = "superuser"
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user_type = "user"

            self.stdout.write(self.style.SUCCESS(f'Successfully created {user_type} "{username}" with access to the chatbot.'))

            if not is_superuser:
                self.stdout.write(
                    self.style.WARNING(
                        "Note: This user can access the chatbot but not the admin panel. "
                        "Use --superuser flag to create an admin user."
                    )
                )

        except ValidationError as e:
            raise CommandError(f"Error creating user: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error: {e}")
