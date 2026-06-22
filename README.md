# Maritime Shipping & Training Academy Backend

A production-ready backend API for a Maritime Shipping & Training Academy platform built with **FastAPI**. This system provides comprehensive functionality for maritime education, trip management, shipping services, online bookings, certifications, payments, and email notifications.

## Features

### Authentication & Authorization

* JWT-based authentication
* Role-based access control (Admin, Trainer, Student)
* Secure password hashing
* Protected API endpoints

### Course Management

* Create, update, delete, and manage courses
* Course enrollment system
* Student progress tracking
* Course completion management
* Certification generation

### Trip Management

* Create and manage maritime trips
* Trip booking system
* Booking status management
* User booking history

### Shipping Services

* Shipping service management
* Service booking functionality
* Public service listings

### Certifications

* Generate certificates for completed courses
* Download certification records
* Student certification history

### Payments

* Stripe payment integration
* Payment verification
* Secure payment processing

### Email Notifications

* Automated email alerts
* Booking confirmation emails
* Course matching notifications
* Welcome emails
* Daily and weekly digest emails

### Background Tasks

* Celery integration
* Redis message broker
* Scheduled tasks with Celery Beat
* Automatic retry mechanism

### Additional Features

* PostgreSQL + PostGIS support
* Dockerized deployment
* RESTful API architecture
* Swagger API documentation
* Comprehensive error handling
* Production-ready configuration

---

## Tech Stack

* **Backend Framework:** FastAPI
* **Database:** PostgreSQL + PostGIS
* **ORM:** SQLAlchemy
* **Authentication:** JWT
* **Task Queue:** Celery
* **Message Broker:** Redis
* **Payments:** Stripe
* **Email Service:** SendGrid
* **Containerization:** Docker & Docker Compose
* **Deployment:** Render
* **Documentation:** Swagger/OpenAPI

---

## Project Structure

```bash
app/
├── api/
│   └── v1/
│       └── endpoints/
├── core/
├── models/
├── schemas/
├── services/
├── tasks/
├── utils/
├── migrations/
└── main.py
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/RehmanAhmad333/Maritime-Shipping-Training-Academy-Backend.git

cd maritime-shipping-training-academy
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file and configure the following:

```env
DATABASE_URL=
SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

SENDGRID_API_KEY=
FROM_EMAIL=

REDIS_URL=redis://localhost:6379/0
```

---

## Database Migration

```bash
alembic upgrade head
```

---

## Run Application

```bash
uvicorn app.main:app --reload
```

Application will be available at:

```bash
http://localhost:8000
```

---

## API Documentation

Swagger Documentation:

```bash
http://localhost:8000/docs
```

ReDoc Documentation:

```bash
http://localhost:8000/redoc
```

---

## Run Celery Worker

```bash
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

## Run Celery Beat

```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

---

## Docker Deployment

Build and start containers:

```bash
docker-compose up --build
```

Run in detached mode:

```bash
docker-compose up -d
```

Stop containers:

```bash
docker-compose down
```

---

## API Modules

* Authentication
* Users
* Courses
* Enrollments
* Certifications
* Trips
* Bookings
* Shipping Services
* Payments
* Email Alerts
* Reviews
* Analytics

---

## Live Deployment

Backend API:

```text
https://maritime-shipping-traning-academy.onrender.com/api/v1
```

Swagger Documentation:

```text
https://maritime-shipping-traning-academy.onrender.com/docs
```

---

## Total API Endpoints

* 58+ REST API Endpoints
* Fully documented with Swagger/OpenAPI

---

## Author

**Rehman Ahmad**

Backend Developer | FastAPI Developer

---

## License

This project is developed for educational and internship purposes.
