# Shared Parking System

A collaborative shared-parking backend API built with **Python 3.11+**, **Django 5.x**, and **Django REST Framework (DRF)**.

The platform provides a peer-to-peer parking spot reservation service where every user can both list parking properties/spaces and reserve spaces listed by others.

---

## Team Roster

| ID | Name | GitHub Handle | Role |
|:---|:---|:---|:---|
| **M1** | Ghanshyam (Lead) | `PaneraGhanshyam` | Repo owner, project foundation & custom user model |
| **M2** | Amit | `Friendly-pro-grammer` | User authentication (register, login, me, delete) |
| **M3** | Dhara | `Dhara-1209` | Property & parking space registration, volume-based pricing |
| **M4** | Kesha | `Kesha-Babriya` | Reservation model, custom QuerySet & viewset skeleton |
| **M5** | Shailesh | `Shailesh7026` | Availability search endpoint & filters |
| **M6** | Yash | `Yash-Soni65` | Reserve a space service (select_for_update & overlap lock) |
| **M7** | Khushboo | `KHUSHBOO1495` | Cancel reservation service & slot release |
| **M8** | Jay | `jaypatel342005` | Testing helpers, CI pipeline, API docs & release |

### Mentors
* **Jeel Patel** (`jeel-patel-scaletech`)
* **Parth Patil** (`parth-patil-scaletech`)

---

## Feature Status

> *Each team member updates only their own row as work progresses.*  
> Status values: `Waiting` → `In Progress` → `In Review` → `Done`

| ID | Feature | Branch | Status | PR Link |
|:---|:---|:---|:---|:---|
| M1 | Project foundation | `chore/project-setup` | In Review | [PR Link](https://github.com/PaneraGhanshyam/shared-parking-system/pulls) |
| M2 | User authentication | `feature/user-auth` | In Review | [PR Link](https://github.com/PaneraGhanshyam/shared-parking-system/pulls) |
| M3 | Property & space registration | `feature/space-registration` | In Review | — |
| M4 | Reservation model | `feature/reservation-model` | Waiting | — |
| M5 | Availability search | `feature/available-spaces-search` | Waiting | — |
| M6 | Reserve a space | `feature/reserve-space` | Waiting | — |
| M7 | Cancel reservation | `feature/cancel-reservation` | Waiting | — |
| M8 | Testing + CI | `ci/test-setup` | In Progress | — |
| M8 | API docs + release | `docs/api-and-seed` | Waiting | — |

---

## Local Setup Guide

Follow these steps to set up and run the project locally:

### 1. Clone the repository
```bash
git clone git@github.com:PaneraGhanshyam/shared-parking-system.git
cd shared-parking-system
```

### 2. Create and activate a virtual environment
```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows (Command Prompt / PowerShell)
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```

### 5. Run migrations
```bash
python manage.py migrate
```

> [!WARNING]
> If you ran `migrate` before M1's custom user model was merged, delete your local `db.sqlite3` and run `python manage.py migrate` again. A database created with Django's built-in user table cannot be switched to the custom one.

### 6. Run tests
```bash
python manage.py test
```

### 7. Start the development server
```bash
python manage.py runserver
```

Verify the health check endpoint:
```bash
curl http://127.0.0.1:8000/api/health/
# Returns: {"status": "ok"}
```

---

## Git Workflow & Contribution Rules

* **Protected `main` Branch**: Never commit directly to `main`. All changes must arrive via Pull Requests.
* **Branch Naming**: `<type>/<short-kebab-name>` (e.g. `feature/user-auth`, `chore/project-setup`, `ci/test-setup`).
* **Conventional Commits**: Format commit messages as:
  ```text
  <type>(<scope>): <subject>

  <optional body explaining why>

  Refs #<issue-number> (or Closes #<issue-number>)
  ```
  * Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `ci`, `style`.
  * Scopes: `setup`, `core`, `auth`, `spaces`, `reservations`, `search`, `docs`, `ci`.
* **Code Reviews**: Every PR requires **2 peer approvals** from assigned reviewers before merging.
* **Merge Policy**: Use **"Create a merge commit"** (`--no-ff`). Do NOT squash or rebase merge on PRs.
