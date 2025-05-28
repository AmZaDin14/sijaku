set dotenv-load

@_default:
  just --list

# Django runserver
serve:
  python manage.py runserver

# Dev
dev:
  bunx concurrently --names "tailwind,django" -c '#f0db4f,#4B8BBE' "python manage.py tailwind start" "python manage.py runserver"

# Build for production
build:
  python manage.py tailwind build
  python manage.py collectstatic --no-input