# 🚀 EdConnect

**EdConnect** is a full-stack mentorship platform that connects students with mentors to foster guidance, career development, and skill growth. It features role-based access for students, mentors, and admins, each with dedicated functionalities.

---

## 🔧 Features

### 👤 User (Student & Mentor)
- Secure authentication with email verification
- Profile creation and editing
- View and connect with available mentors
- One-to-one chat with mentors
- Booking slots for mentorship sessions

### 🧑‍🏫 Mentor
- Detailed mentor profile with document uploads
- Slot management (availability for sessions)
- Manage incoming connection requests
- Accept/reject mentorship requests

### 🛡️ Admin
- View all registered users and mentors
- Verify/reject mentor documents
- Manage platform content and user reports

---

## 🛠️ Tech Stack

### ⚙️ Backend
- Django + Django REST Framework
- PostgreSQL
- Redis + Celery (for async tasks)
- Nginx + Gunicorn (for production)
- Docker + Docker Compose

### 🌐 Frontend
- React (Vite) + TypeScript
- Tailwind CSS + ShadCN UI

---


### 1️To Enter Django container
```bash
docker exec -it django_app bash

docker exec -it postgres_db psql -U myuser -d mydb

