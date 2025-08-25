# 🚀 EdConnect

**EdConnect** is a full-stack platform designed to bridge the gap between students aspiring to study abroad and those already enrolled in foreign universities. The platform enables seamless mentorship, personalized guidance, and meaningful connections, helping students navigate their journey to global education with confidence.

---

## 🎯 Purpose

Many students dream of studying abroad but face challenges such as lack of proper guidance, understanding application processes, and preparing for academic and cultural transitions. **EdConnect** solves this by connecting them with verified mentors—students currently pursuing education in foreign universities—who can provide authentic advice, share experiences, and guide them step-by-step through their journey.

---

## 👥 Target Users

- **Aspiring Students**: High school or college students planning to study abroad.
- **Mentors**: Students currently studying in foreign universities who wish to guide others.
---

## 🔧 Key Features

### 👤 Student (User)
- Secure signup and login with **email verification**
- Create and edit a personal profile
- Discover and filter mentors by **university, country, course, or experience**
- Send and manage **mentorship connection requests**
- Engage in **one-on-one chat** with mentors
- **Book mentorship slots** based on mentor availability

### 🧑‍🏫 Mentor
- Build a detailed **mentor profile** (course, university, background)
- Upload documents for **admin verification**
- **Set and manage availability slots** for student sessions
- **Accept or reject** incoming mentorship requests
- Respond to student queries via **chat interface**

### 🛡️ Admin
- Manage and monitor all **users and mentors**
- **Verify or reject mentor documents** and profiles
- Handle **platform-level content** and user-generated reports
- Ensure **authenticity and trustworthiness** of mentor information

---

## ⚙️ Tech Stack

### 🔙 Backend
- **Django** & **Django REST Framework** – for API development
- **PostgreSQL** – relational database
- **Redis** & **Celery** – background task processing (e.g., email verification)
- **Docker + Docker Compose** – containerized development and deployment
- **Gunicorn** & **Nginx** – WSGI server and reverse proxy for production

### 🌐 Frontend
- **React (Vite) + TypeScript** – modern frontend with optimized performance
- **Tailwind CSS** + **ShadCN UI** – responsive and professional design system

---

## 🧪 Development Workflow

### 🐳 Accessing Docker Services

#### Django Container:
```bash
docker exec -it django_app bash

#### Database Container:
```bash
docker exec -it postgres_db psql -U myuser -d mydb


stripe listen --forward-to localhost/api/bookings/stripe-webhook/