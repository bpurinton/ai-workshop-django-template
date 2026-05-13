# AGENTS.md

Guidance for AI coding agents (Claude Code, Cursor, Codex, Aider, etc.) working in
this repository. Humans: see `README.md` for the friendlier overview.

## What this project is

A minimal Django starter template designed to be opened in **GitHub Codespaces**.
It pairs a Python dev container with a Postgres service so a student can clone,
launch a codespace, and have a runnable Django project in one step.

- **Django**: 5.2 LTS
- **Python**: 3.12
- **Database**: PostgreSQL 16 (provided by the dev container's compose file)
- **Server**: `python manage.py runserver` for development

The Django project package is named `project_config` (not the conventional
`config` or the project name) — keep that in mind when writing imports.

## Repository layout

```
.
├── .devcontainer/        # Codespaces / dev container definition (do not rename)
│   ├── devcontainer.json
│   ├── docker-compose.yml
│   └── Dockerfile
├── project_config/       # Django project package (settings, urls, asgi, wsgi)
│   ├── settings.py
│   └── urls.py
├── manage.py
├── requirements.txt
└── AGENTS.md             # ← you are here
```

New Django apps should be created at the **repository root** (siblings of
`project_config/`), not nested inside `project_config/`. Example:

```bash
python manage.py startapp blog
```

Then register the app in `project_config/settings.py` `INSTALLED_APPS` and wire
its URLs into `project_config/urls.py`.

## How to run things

All commands assume you are inside the dev container (the default Codespaces
shell). The Postgres service is already running and `DATABASE_URL` is already
set via `containerEnv` in `.devcontainer/devcontainer.json`.

| Task                       | Command                                              |
| -------------------------- | ---------------------------------------------------- |
| Install / refresh deps     | `pip install --user -r requirements.txt`             |
| Apply migrations           | `python manage.py migrate`                           |
| Create a new app           | `python manage.py startapp <name>`                   |
| Make migrations            | `python manage.py makemigrations`                    |
| Run the dev server         | `python manage.py runserver 0.0.0.0:8000`            |
| Open a Django shell        | `python manage.py shell`                             |
| Create a superuser         | `python manage.py createsuperuser`                   |
| Run the test suite         | `python manage.py test`                              |
| Format Python with Black   | `black .`                                            |

The dev server **must** bind to `0.0.0.0:8000` (not `127.0.0.1`) for Codespaces
port forwarding to expose it on the "Live App Preview" port.

## Conventions

- **Formatting**: Black, default settings. Run `black .` before committing.
- **Quote style**: double quotes (Black's default).
- **Imports**: standard library, third-party, local — separated by blank lines.
- **Settings**: read configuration from environment variables via `os.environ`
  and `dj_database_url.config()`. Do not hardcode secrets, hosts, or database
  URLs in `settings.py` beyond what's already there.
- **CSRF / hosts**: `ALLOWED_HOSTS_ALL=1` is set in the dev container so the
  Codespaces forwarded URL works. Do not remove that branch in `settings.py`.
- **Migrations**: always commit migration files alongside the model changes
  that produced them. Never edit applied migrations by hand.
- **Templates**: app-local under `<app>/templates/<app>/`. If you add a
  project-wide `templates/` directory, register it in `TEMPLATES[0]["DIRS"]`.
- **Static files**: app-local under `<app>/static/<app>/`. `STATIC_URL` is
  already set; use `whitenoise` patterns if you add `STATICFILES_STORAGE`.

## Don't touch unless asked

- `.devcontainer/` — changing this can break Codespaces startup for students.
- The hardcoded `SECRET_KEY` in `settings.py` — this template is intentionally
  insecure for workshop use. Real deployments should override via env var, but
  don't rewrite this for the template itself.
- `project_config/` package name — renaming requires coordinated edits across
  `manage.py`, `wsgi.py`, `asgi.py`, `settings.py`, and `DJANGO_SETTINGS_MODULE`.

## When asked to add a feature

1. Check whether a Django app already exists for it. If not, run
   `python manage.py startapp <name>` from the repo root.
2. Add the app to `INSTALLED_APPS` in `project_config/settings.py`.
3. Add models → run `makemigrations` → run `migrate`.
4. Add views/templates/urls.
5. Include the app's `urls.py` from `project_config/urls.py` via `include()`.
6. Verify with `python manage.py runserver 0.0.0.0:8000` and visit the
   forwarded port.

## When something looks wrong

- **`runserver` exits immediately or "DisallowedHost"** — confirm
  `ALLOWED_HOSTS_ALL=1` is in the environment (it should be, via devcontainer).
- **`could not connect to server`** — the Postgres container may not be up.
  In Codespaces, rebuild the container; locally, `docker compose up db`.
- **Import errors after install** — `pip install --user -r requirements.txt`
  again; the `--user` flag matters inside this container.
