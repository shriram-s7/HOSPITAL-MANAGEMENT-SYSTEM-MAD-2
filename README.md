# Hospital Management System (MAD 2)

A single-page hospital management app built for the IITM BS *Modern Application Development 2* course: a **Flask REST API** with JWT login and a **Vue 3** front end, plus **Celery + Redis** background jobs for email reminders, a monthly report and CSV export.

## What it does

Three roles, each with its own dashboard:

- **Admin**: dashboard totals; create, edit and delete departments, doctors and patients; view all appointments.
- **Doctor**: set availability; see assigned appointments; mark them completed or cancelled; add a treatment record (diagnosis, prescription, notes); view a patient's history.
- **Patient**: register and log in; edit profile; browse doctors; book and cancel appointments; request a CSV export of their treatment history.

Background jobs (Celery):

- `daily_reminders`: every day at 08:00, emails appointment reminders.
- `monthly_report`: on the 1st of each month at 08:00, emails an activity report.
- `export_csv_job`: builds and emails a patient's treatment-history CSV on request.

## Stack

| Layer | Technology |
|---|---|
| API | Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS, Flask-Caching |
| Database | SQLite (`backend/hms.db`, created on first run); `DATABASE_URL` can override |
| Cache / queue | Redis (broker and result backend on db 0, cache on db 1) |
| Jobs | Celery worker and Celery beat |
| Front end | Vue 3, Vue Router, Axios, Bootstrap 5, Vite |

## Run it

Prerequisites: Python 3, Node.js, and a Redis server on `localhost:6379`.

```bash
# 1. Python environment (from the project root)
python -m venv venv
venv\Scripts\activate            # Windows
pip install flask flask-sqlalchemy flask-jwt-extended flask-cors flask-caching celery redis

# 2. Terminal 1: front end
cd frontend
npm install
npm run dev

# 3. Terminal 2: API (http://127.0.0.1:5000/api)
cd backend
python app.py

# 4. Terminal 3: Celery (optional, needs Redis)
cd backend
python -m celery -A celery_worker.celery worker --loglevel=info -P solo
python -m celery -A celery_worker.celery beat --loglevel=info      # scheduled jobs
```

`python backend/seed.py` loads sample departments and doctors. On first start the API creates an `admin` user (default password defined in `backend/app.py`; change it for any real use). `setup.txt` and `fix+setup.txt` hold the author's quick command notes.

## Configuration (environment variables)

| Variable | Purpose |
|---|---|
| `SECRET_KEY`, `JWT_SECRET_KEY` | Flask and JWT signing keys (a development default is used if unset) |
| `DATABASE_URL` | Optional database URL instead of the bundled SQLite file |
| `HMS_SENDER_PASSWORD` | App password for the Gmail sender address used by the Celery email jobs. Without it, emails are not sent |

Never commit real keys or passwords; `.env` files are git-ignored.

## Layout

```
backend/    app.py, config.py, models.py, routes.py, seed.py, celery_worker.py
frontend/   Vue 3 + Vite app (src/views: Login, AdminDashboard, DoctorDashboard, PatientDashboard)
24f3004661 Project Report.pdf    course project report
```
