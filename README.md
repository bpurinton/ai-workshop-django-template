# ai-workshop-django-template

A Django 5.2 starter template designed to open in a **GitHub Codespace** and be
productive with AI coding assistants from minute one.

Originally inspired by [Simon Willison's TIL on Django + Postgres in
Codespaces](https://til.simonwillison.net/github/django-postgresql-codespaces).

## What's in the box

- **Django 5.2 LTS** (supported through April 2028)
- **Python 3.12** dev container
- **PostgreSQL 16** running as a sidecar service
- Pre-configured Codespaces port forwarding for `localhost:8000`
- `AGENTS.md` so Claude Code, Cursor, Codex, etc. know the conventions

## Quick start (Codespaces)

1. Click **Use this template → Create a new repository**.
2. From the new repo, click **Code → Codespaces → Create codespace on main**.
3. Wait for the post-create step to finish (`pip install -r requirements.txt`).
4. In the codespace terminal:

   ```bash
   python manage.py migrate
   python manage.py runserver 0.0.0.0:8000
   ```

5. Open the forwarded port labelled **Live App Preview** in the Ports panel.
   You should see Django's "It worked!" page.

## Quick start (local, without Codespaces)

You need Docker Desktop and the **Dev Containers** VS Code extension.

```bash
git clone <your-repo-url>
cd <your-repo>
code .                  # then: "Reopen in Container" from the command palette
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Adding your first app

```bash
python manage.py startapp blog
```

Then in `project_config/settings.py`:

```python
INSTALLED_APPS = [
    ...,
    "blog",
]
```

And in `project_config/urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("blog/", include("blog.urls")),
]
```

## Common commands

| What                       | Command                                              |
| -------------------------- | ---------------------------------------------------- |
| Apply migrations           | `python manage.py migrate`                           |
| Create new migrations      | `python manage.py makemigrations`                    |
| Start a new app            | `python manage.py startapp <name>`                   |
| Dev server                 | `python manage.py runserver 0.0.0.0:8000`            |
| Django shell               | `python manage.py shell`                             |
| Create admin user          | `python manage.py createsuperuser`                   |
| Run tests                  | `python manage.py test`                              |
| Format code                | `black .`                                            |

## Project layout

```
.
├── .devcontainer/        # Codespaces config: Dockerfile + compose + devcontainer.json
├── project_config/       # Django project package (settings, urls, asgi, wsgi)
├── manage.py
├── requirements.txt
├── AGENTS.md             # Conventions for AI coding agents
└── README.md
```

## Working with AI agents

This template ships with an [`AGENTS.md`](AGENTS.md) that documents the project
conventions, layout, and common commands in a format agents can pick up
automatically. It works with Claude Code, Cursor, Codex, Aider, and any tool
that follows the [AGENTS.md convention](https://agents.md).

## License

Some rights reserved — see [LICENSE.txt](LICENSE.txt).
