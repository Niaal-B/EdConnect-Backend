# Django + React Starter Kit

A robust and scalable starter kit for building full-stack applications using **Django** (Dockerized backend with Gunicorn, Redis, Celery, and PostgreSQL) and **React (TypeScript)** (frontend outside Docker). This setup is production-ready with modularity and flexibility for various project types.

---

## Features

* **Backend:** Django with Docker, Gunicorn, Redis, Celery, and PostgreSQL.
* **Frontend:** React (TypeScript) running locally, communicating with the backend API.
* **Reverse Proxy:** Nginx serving static files and proxying requests to Gunicorn.
* **Background Tasks:** Celery with Redis for handling asynchronous tasks (like OTP/email sending).
* **Secure and Scalable:** Production-ready settings with environment-based configuration.
* **Modularity:** Easily reusable for any Django + React project.

---

## Project Structure

```
├── backend/           # Django backend app & Docker setup
├── frontend/          # React (TypeScript) app (run locally)
├── nginx/             # Nginx config for serving static files & proxy
├── docker-compose.yml # Compose file for backend, db, redis, nginx
└── README.md          # Project documentation
```

---

## Prerequisites

* Docker & Docker Compose installed
* Node.js and npm/yarn installed (for React frontend)

---

## Setup

### Backend Setup (Dockerized Django)

1. Clone the repo:

```bash
git clone https://github.com/yourusername/django-react-starter.git
cd django-react-starter/backend
```

2. Create a `.env` file for sensitive variables:

```env
DB_NAME=yourdbname
DB_USER=yourdbuser
DB_PASSWORD=yourdbpassword
REDIS_HOST=redis_server
CELERY_BROKER_URL=redis://redis_server:6379/0
```

3. Build and start all services:

```bash
docker-compose up --build
```

4. Run Django migrations:

```bash
docker exec -it django_app python manage.py migrate
```

5. Collect static files:

```bash
docker exec -it django_app python manage.py collectstatic --noinput
```

6. Your Django backend will be running at: `http://localhost`

---

### Frontend Setup (React TSX)

1. Navigate to the frontend folder:

```bash
cd ../frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start React development server:

```bash
npm start
```

4. Your React app will run at: `http://localhost:3000` and communicate with Django backend API.

---

## Using Celery (Optional)

1. Define your Celery tasks in `backend/tasks.py`.

2. Trigger tasks using Django views or signals.

3. Use Redis as the message broker for Celery tasks.

---

## Troubleshooting

* Ensure Docker containers are running (`docker ps`).
* Verify Redis and Celery are connected for background tasks.
* Check Nginx for static file serving issues.
* For React API calls, ensure CORS is correctly configured.

---

## License

MIT License © 2025 Nihal
