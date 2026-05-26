# Breathe ESG Tech Intern Assignment

Prototype for ingesting enterprise ESG activity data from SAP, utility electricity exports, and corporate travel systems, normalizing it, and presenting an analyst review dashboard before records are locked for audit.

## Stack

- Django + Django REST Framework
- SQLite for the prototype database
- React + Vite

## Local Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

```bash
cd frontend
npm install
npm run dev
```

The API runs on `http://127.0.0.1:8000/api/`.
The UI runs on `http://127.0.0.1:5173/`.

## Demo Login

This prototype does not require authentication locally. The data model is tenant-aware and every API response is scoped to the demo tenant.

## Deployment Notes

The app is split into `backend` and `frontend` so it can be deployed on Render/Railway as two services:

- Backend: Python web service, build `pip install -r requirements.txt`, start `gunicorn breathe.wsgi:application`
- Frontend: Static site, build `npm install && npm run build`, publish `dist`

If using the included `render.yaml` Blueprint, Render wires the frontend API URL to the backend service automatically.
If creating services manually, set `VITE_API_BASE_URL` on the frontend to the deployed backend `/api` URL.
