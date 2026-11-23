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
| M1 | Project foundation | `chore/project-setup` | Done | [#3](https://github.com/PaneraGhanshyam/shared-parking-system/pull/3) |
| M2 | User authentication | `feature/user-auth` | Done | [#14](https://github.com/PaneraGhanshyam/shared-parking-system/pull/14) |
| M3 | Property & space registration | `feature/space-registration` | Done | [#13](https://github.com/PaneraGhanshyam/shared-parking-system/pull/13) |
| M4 | Reservation model | `feature/reservation-model` | Done | [#15](https://github.com/PaneraGhanshyam/shared-parking-system/pull/15) |
| M5 | Availability search | `feature/available-spaces-search` | Done | [#17](https://github.com/PaneraGhanshyam/shared-parking-system/pull/17) |
| M6 | Reserve a space | `feature/reserve-space` | Done | [#16](https://github.com/PaneraGhanshyam/shared-parking-system/pull/16) |
| M7 | Cancel reservation | `feature/cancel-reservation` | Done | [#18](https://github.com/PaneraGhanshyam/shared-parking-system/pull/18) |
| M8 | Testing + CI | `ci/test-setup` | Done | [#12](https://github.com/PaneraGhanshyam/shared-parking-system/pull/12) |
| M8 | API docs + release | `docs/api-and-seed` | Done | [#19](https://github.com/PaneraGhanshyam/shared-parking-system/pull/19) |

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

### 8. Seed demo data (Optional)
Populate sample users (`ravi`, `priya`, `rahul`), properties, and spaces of mixed vehicle types (`CAR`, `BIKE`, `TRUCK`):
```bash
python manage.py seed_demo_data
```

### 9. Interactive API Documentation
Explore the interactive Swagger UI and schema:
- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/

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

---

## API Examples (curl)

### 1. Health Check
```bash
curl -X GET http://127.0.0.1:8000/api/health/
```

### 2. User Authentication

#### Register Account
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ravi",
    "email": "ravi@example.com",
    "password": "securePass123",
    "phone_number": "+919876543210"
  }'
```

#### Login (Obtain Token)
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ravi",
    "password": "securePass123"
  }'
```
*Response returns auth token: `{"token": "<TOKEN>", "user_id": 1, "username": "ravi"}`*

#### Current User Profile
```bash
curl -X GET http://127.0.0.1:8000/api/auth/me/ \
  -H "Authorization: Token <TOKEN>"
```

### 3. Properties & Parking Spaces

#### Register a Property
```bash
curl -X POST http://127.0.0.1:8000/api/properties/ \
  -H "Authorization: Token <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Ravi'\''s Home",
    "description": "Gated society, ground-floor parking",
    "address": "12 Lake View Society",
    "city": "Ahmedabad",
    "state": "Gujarat",
    "postal_code": "380015"
  }'
```

#### List My Properties
```bash
curl -X GET http://127.0.0.1:8000/api/properties/ \
  -H "Authorization: Token <TOKEN>"
```

#### Register a Space (Automatic Pricing based on dimensions)
```bash
curl -X POST http://127.0.0.1:8000/api/spaces/ \
  -H "Authorization: Token <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "parking_property": 1,
    "spot_label": "A1",
    "vehicle_type": "CAR",
    "length_cm": 500,
    "width_cm": 250,
    "height_cm": 200
  }'
```
*Price per hour calculated automatically: `(500 * 250 * 200) / 1,000,000 * ₹2.00 = ₹50.00/hr`.*

### 4. Search Available Spaces
```bash
curl -X GET "http://127.0.0.1:8000/api/spaces/available/?start=2026-11-25T09:00:00Z&end=2026-11-25T11:00:00Z&city=Ahmedabad&vehicle_type=CAR" \
  -H "Authorization: Token <TOKEN>"
```

### 5. Reservations

#### Reserve a Space
```bash
curl -X POST http://127.0.0.1:8000/api/reservations/ \
  -H "Authorization: Token <CUSTOMER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "space": 1,
    "start_time": "2026-11-25T09:00:00Z",
    "end_time": "2026-11-25T11:00:00Z"
  }'
```

#### List My Reservations
```bash
curl -X GET http://127.0.0.1:8000/api/reservations/ \
  -H "Authorization: Token <CUSTOMER_TOKEN>"
```

#### Cancel a Reservation
```bash
curl -X POST http://127.0.0.1:8000/api/reservations/1/cancel/ \
  -H "Authorization: Token <CUSTOMER_TOKEN>"
```

### 6. Account Deactivation (Soft Delete)
```bash
curl -X DELETE http://127.0.0.1:8000/api/auth/me/ \
  -H "Authorization: Token <TOKEN>"
```

