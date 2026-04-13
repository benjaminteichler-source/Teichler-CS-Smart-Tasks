# Smart Task Manager

A production-ready web application for managing tasks, built with **Flask (Python)**, **SQLite**, and plain HTML/CSS/JS. Designed to demonstrate strong SDLC principles, modular architecture, and advanced Python features.

---

## Features

- **Create / Edit / Delete** tasks with title, description, category, priority, and due date
- **Mark tasks complete / incomplete** with a single click
- **Filter** tasks by category, priority, or keyword search
- **Stats bar** showing total, completed, pending, and overdue counts
- **Overdue detection** — tasks past their due date are highlighted in red
- **Flash feedback** — user-friendly success / error messages for every action
- **Client-side validation** — JavaScript pre-validates forms; server always validates too
- **Fully responsive** — usable on mobile and desktop

---

## Folder Structure

```
smart_task_manager/
├── app.py                   # Application factory + entry point
├── config.py                # Environment-based configuration
├── Procfile                 # gunicorn start command for Railway
├── requirements.txt         # Python dependencies
├── README.md
│
├── models/
│   ├── __init__.py
│   └── task.py              # Task @dataclass + custom exceptions
│
├── database/
│   ├── __init__.py
│   └── db.py                # All SQL — context-manager connection, CRUD helpers
│
├── routes/
│   ├── __init__.py
│   └── task_routes.py       # Flask Blueprint — HTTP layer only
│
├── services/
│   ├── __init__.py
│   └── task_service.py      # Business logic, @decorator, generator
│
├── templates/
│   ├── base.html            # Shared layout with header, flash messages, footer
│   ├── index.html           # Task list, stats, add-task form, filter bar
│   └── edit.html            # Edit-task form
│
├── static/
│   ├── style.css            # Full responsive stylesheet
│   └── script.js            # Progressive-enhancement JS (validation, confirm)
│
└── tests/
    ├── __init__.py
    ├── conftest.py          # pytest path + env setup
    └── test_tasks.py        # 28 test cases across 4 test classes
```

---

## Running Locally

```bash
# 1. Clone / enter the project directory
cd smart_task_manager

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the development server
python app.py
# → Open http://localhost:5000
```

The SQLite database file (`tasks.db`) is created automatically on first run.

---

## Running Tests

```bash
# From the project root:
pytest tests/ -v

# With coverage (optional):
pip install pytest-cov
pytest tests/ -v --cov=. --cov-report=term-missing
```

Expected output: **28 tests, all passing**.

---

## Architecture & Design Decisions

The application is organised in strict **horizontal layers**. Each layer only ever calls the layer directly below it; no layer skips a level.

```
HTTP Request
     │
     ▼
 routes/           ← parse request, flash messages, redirect / render
     │
     ▼
 services/         ← business rules, input validation, filtering
     │
     ▼
 database/         ← raw SQL, connection management
     │
     ▼
 models/           ← pure data structures, no I/O
```

| Layer | File | Responsibility |
|---|---|---|
| **Model** | `models/task.py` | Pure data — no DB, no HTTP |
| **Database** | `database/db.py` | All raw SQL; single connection context manager |
| **Service** | `services/task_service.py` | Business rules, validation, filtering |
| **Routes** | `routes/task_routes.py` | HTTP request/response only; delegates to services |
| **Config** | `config.py` | Per-environment settings selected via `FLASK_ENV` |

This separation means the **service layer can be fully unit-tested without Flask or a real database** — the tests use an in-memory SQLite instance configured in `config.py`.

---

## Advanced Python Features Used

| Feature | Location | How it's used |
|---|---|---|
| **`@dataclass`** | `models/task.py` | `Task` class with typed fields, `__post_init__` normalisation, computed properties (`is_overdue`, `priority_badge`) |
| **Custom exceptions** | `models/task.py` | `InvalidTaskError` — bad user input; `TaskNotFoundError` — missing DB record |
| **Decorator** | `services/task_service.py` | `@validate_task_input` — validates `title` and `due_date` before the wrapped function executes; reused on both `create_task` and `edit_task` |
| **Generator** | `services/task_service.py` | `filter_tasks()` — lazily `yield`s matching tasks, avoiding a full copy of the list when filters are strict |
| **Type hints** | Throughout | All function signatures annotated; `Optional`, `List`, `Generator`, `Callable` from `typing` |

---

## Deploying to Railway

### Prerequisites
- [Railway account](https://railway.app) (free tier works)
- Git installed locally
- GitHub account

### Step-by-step

```bash
# ── 1. Initialise a Git repository ───────────────────────────────────────────
cd smart_task_manager
git init
git add .
git commit -m "Initial commit: Smart Task Manager"

# ── 2. Push to GitHub ─────────────────────────────────────────────────────────
# Option A — using the GitHub CLI
gh repo create smart-task-manager --public --source=. --push

# Option B — manually
#   1. Create a new repo at https://github.com/new (no README, no .gitignore)
#   2. Then run:
git remote add origin https://github.com/<YOUR_USERNAME>/smart-task-manager.git
git branch -M main
git push -u origin main
```

```
# ── 3. Create a Railway project ───────────────────────────────────────────────
# Go to https://railway.app → click "New Project"

# ── 4. Link your GitHub repository ────────────────────────────────────────────
# Select "Deploy from GitHub repo" → authorise Railway → choose your repo.
# Railway detects Python automatically and reads the Procfile.

# ── 5. Set environment variables (optional but recommended) ───────────────────
# In the Railway dashboard → your service → Variables tab → add:
#   SECRET_KEY   =  <a long random string, e.g. output of: python -c "import secrets; print(secrets.token_hex(32))">
#   FLASK_ENV    =  production

# ── 6. Confirm start command ──────────────────────────────────────────────────
# Railway reads Procfile automatically:
#   web: gunicorn app:app
# No additional configuration needed.

# ── 7. Deploy ─────────────────────────────────────────────────────────────────
# Railway triggers a build and deploy on every push to `main`.
# Your public URL appears in the dashboard under "Deployments".
```

> **SQLite on Railway:** Railway's filesystem is ephemeral — the `.db` file resets on each redeploy. This is fine for development and grading. For a production deployment requiring persistence, add a **Railway PostgreSQL** database plugin and update `database/db.py` to use `psycopg2`.

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| Flask | 3.0.3 | Web framework |
| gunicorn | 22.0.0 | Production WSGI server |
| pytest | 8.2.2 | Test runner |

---

*Built with Python 3.10+ · Flask · SQLite*
