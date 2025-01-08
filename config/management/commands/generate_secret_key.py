import os

from django.core.management.base import BaseCommand, CommandError
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = "Generate a new Django secret key and save it to a .env file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default=".env",
            help="Path to the .env file (default: .env in the project root)",
        )

    def handle(self, *args, **options):
        path = options["path"]
        secret_key = get_random_secret_key()

        try:
            self.save_to_env(path, secret_key)
            self.stdout.write(
                self.style.SUCCESS(f"Secret key generated and saved to {path}")
            )
        except Exception as e:
            raise CommandError(f"Failed to write to {path}: {e}")

    def save_to_env(self, path, secret_key):
        """Save the secret key to the specified .env file."""
        env_line = f'SECRET_KEY="{secret_key}"\n'

        # Check if .env file exists
        if os.path.exists(path):
            with open(path, "r") as file:
                lines = file.readlines()

            # Check if SECRET_KEY already exists
            for i, line in enumerate(lines):
                if line.startswith("SECRET_KEY="):
                    lines[i] = env_line
                    break
            else:
                lines.append(env_line)

            with open(path, "w") as file:
                file.writelines(lines)
        else:
            # Create a new .env file with the SECRET_KEY
            with open(path, "w") as file:
                file.write(env_line)
