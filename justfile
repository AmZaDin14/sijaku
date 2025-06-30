set dotenv-load

@_default:
  just --list

# Migrate
migrate:
  python manage.py makemigrations && python manage.py migrate

# Create a superuser
su:
  python manage.py createsuperuser

# Django runserver
serve:
  python manage.py runserver

# Dev
dev:
  bunx concurrently --names "tailwind,django" -c '#f0db4f,#4B8BBE' "python manage.py tailwind start" "python manage.py runserver"

devel:
  bunx concurrently --names "tailwind,django" -c '#f0db4f,#4B8BBE' "python manage.py tailwind start" "uvicorn config.asgi:application --reload"

compose:
  podman compose down && podman compose up -d

# Build for production
build:
  python manage.py tailwind build
  python manage.py collectstatic --no-input
