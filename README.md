# EdConnect

[![Build Status](https://img.shields.io/github/workflow/status/Niaal-B/EdConnectCI)](https://github.com/Niaal-B/EdConnectactions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Contributors](https://img.shields.io/github/contributors/Niaal-B/EdConnect)](https://github.com/username/edconnect/graphs/contributors)

A full-stack mentorship platform connecting aspiring international students with mentors currently studying abroad.

## Overview

EdConnect bridges the information gap for students planning to study abroad by facilitating direct connections with peers who are already navigating international universities. The platform enables meaningful mentorship relationships through structured matching, real-time communication, and administrative oversight.

Students gain access to first-hand insights about university life, application processes, and cultural adaptation, while mentors can share their experiences and contribute to the next generation of international students.

## Features

### Student Experience
- Profile creation with academic background and study abroad goals
- Browse mentor profiles filtered by university, field of study, and location
- Send connection requests and schedule mentorship sessions
- Real-time messaging with matched mentors
- Access to curated resources and guides

### Mentor Platform
- Comprehensive profile setup showcasing university and expertise
- Availability management for mentorship sessions
- Student request handling and connection management
- Progress tracking for mentoring relationships
- Resource sharing capabilities

### Administrative Tools
- User verification system for mentors and students
- Platform analytics and usage monitoring
- Content moderation and user support
- Feature management and system configuration

## Technology Stack

### Backend Infrastructure
- **Framework**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL 15+
- **Caching**: Redis 7.0+
- **Task Processing**: Celery with Redis broker
- **Authentication**: JWT with Django Simple JWT

### Frontend Application
- **Framework**: React 18+ with TypeScript
- **Build System**: Vite 4+
- **Styling**: Tailwind CSS 3.3+
- **Components**: ShadCN UI
- **State Management**: React Query + Zustand

### Deployment & Operations
- **Containerization**: Docker and Docker Compose
- **Web Server**: Nginx (reverse proxy)
- **WSGI Server**: Gunicorn
- **Runtime**: Python 3.11+, Node.js 18+

## Installation

### Requirements
- Docker and Docker Compose
- Python 3.11 or higher
- Node.js 18 or higher
- Git

### Quick Start

Clone the repository:
```bash
git clone https://github.com/username/edconnect.git
cd edconnect
```

Set up environment variables:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Configure your environment files with appropriate values for database connections, API keys, and service URLs.

Start the application with Docker:
```bash
docker-compose up --build
```

Initialize the database:
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- Admin interface: http://localhost:8000/admin

### Manual Development Setup

For local development without Docker:

**Backend setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend setup:**
```bash
cd frontend
npm install
npm run dev
```

**Required services:**
- PostgreSQL database running on port 5432
- Redis server running on port 6379
- Celery worker process for background tasks


## 🧪 Development Workflow

### 🐳 Accessing Docker Services

#### Django Container
```bash
docker exec -it django_app bash
Database Container
bash
Copy
Edit
docker exec -it postgres_db psql -U myuser -d mydb
💳 Stripe Webhooks
Run the following command to listen for Stripe events and forward them to your local API:

bash
Copy
Edit
stripe listen --forward-to localhost/api/bookings/stripe-webhook/

## Usage

### Getting Started

After installation, create your first account through the web interface. Students should complete their academic profile including target universities and areas of interest. Mentors need to verify their current university enrollment and specify their areas of expertise.

The matching system considers factors like academic discipline, target universities, and geographical preferences to suggest relevant mentor-student connections.

### Development Workflow

Create a feature branch for new development:
```bash
git checkout -b feature/your-feature-name
```

Run the test suite before submitting changes:
```bash
# Backend tests
docker-compose exec backend python manage.py test

# Frontend tests
docker-compose exec frontend npm run test
```

Follow the existing code style and ensure all tests pass before creating a pull request.

### Docker Services

Access running services for debugging:
```bash
# Backend application shell
docker-compose exec backend python manage.py shell

# View application logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Development Roadmap

### Short Term
- Enhanced matching algorithm using machine learning

### Medium Term
- Group mentorship sessions and webinar capabilities
- Advanced analytics for tracking student progress

### Long Term
- AI-powered chatbot for initial student guidance
- Integration with university databases for automatic verification
- Multi-language support for global accessibility

## Contributing

We welcome contributions from developers, designers, and domain experts. Please read our contributing guidelines and code of conduct before submitting pull requests.

### Areas for Contribution
- Bug fixes and performance improvements
- New feature development
- Documentation updates
- User interface enhancements
- Testing and quality assurance

### Issue Reporting

When reporting bugs or requesting features, please provide:
- Clear description of the issue or desired functionality
- Steps to reproduce (for bugs)
- Expected behavior vs actual behavior
- Environment details (operating system, browser, etc.)

## License

This project is licensed under the MIT License. See the LICENSE file for full terms and conditions.

## Support

For technical issues, feature requests, or general questions:
- Create an issue in the GitHub repository
- Check existing documentation and FAQ
- Contact the development team through established channels

The project maintains active development with regular updates and community engagement through GitHub discussions and issue tracking.