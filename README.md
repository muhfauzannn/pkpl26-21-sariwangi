# Sariwangi - Django Project

## Setup

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

3. Run the development server:

```bash
python manage.py runserver
```

## Settings Environments

The project uses split settings located in `config/settings/`:

- **development** (default) — `config.settings.development` — DEBUG=True, SQLite, all hosts allowed
- **production** — `config.settings.production` — DEBUG=False, secure cookies, HSTS, SSL redirect

To switch, set `DJANGO_SETTINGS_MODULE` in `.env`:

```
DJANGO_SETTINGS_MODULE=config.settings.production
```

Or pass it when running manage.py:

```bash
DJANGO_SETTINGS_MODULE=config.settings.production python manage.py runserver
```

## Static Files

### Development

Static files in `static/` are served automatically by Django when `DEBUG=True`. No need to run `collectstatic`. Just use `{% load static %}` in templates:

```html
{% load static %}
<link rel="stylesheet" href="{% static 'css/base.css' %}">
```

### Production

WhiteNoise serves static files in production with compression and caching. Run `collectstatic` once during deployment:

```bash
python manage.py collectstatic --noinput
```

This collects files from `static/` and any app `static/` directories into `staticfiles/`.

## Media Files

User-uploaded files are stored in `media/` and served at `/media/` during development. In production, configure your web server (nginx, etc.) to serve media files, or use a cloud storage backend.

## Project Structure

```
├── config/             # Project configuration
│   ├── settings/       # Split settings (base, development, production)
│   ├── urls.py         # Root URL configuration
│   ├── wsgi.py         # WSGI entry point
│   └── asgi.py         # ASGI entry point
├── apps/               # Django apps (add future apps here)
├── static/             # Project-level static files (css, js, images)
├── media/              # User-uploaded media files
├── templates/          # Project-level templates
├── manage.py
├── requirements.txt
├── .env.example
└── .gitignore
```

## Adding a New App

```bash
python manage.py startapp myapp apps/myapp
```

Then add `"apps.myapp"` to `INSTALLED_APPS` in `config/settings/base.py`.
