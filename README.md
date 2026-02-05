# 🎬 Online Cinema Platform

An Online Cinema is a modern digital platform that allows users to browse, purchase, and watch movies online.  
This project is a backend service built with **FastAPI** and designed using **clean architecture**, **async-first principles**, and **scalable microservice-friendly patterns**.

The system supports user authentication, movie catalog management, shopping carts, orders, payments, and role-based access control.

---

## 🚀 Tech Stack

### Backend
- **Python 3.11**
- **FastAPI** (async REST API)
- **SQLAlchemy 2.0 (async)**
- **Alembic (async migrations)**
- **PostgreSQL** (main database)
- **Redis** (Celery broker & cache)
- **Celery + Celery Beat** (background tasks & periodic jobs)
- **JWT (Access & Refresh tokens)**

### Infrastructure
- **Docker & Docker Compose**
- **Poetry** (dependency management)
- **GitHub Actions** (CI/CD)
- **AWS EC2** (deployment target)
- **MinIO** (S3-compatible storage for avatars/media)

### Payments
- **Stripe**
- Webhook-based payment validation

---

## 🧩 Core Features

### 👤 Accounts & Authentication
- Email-based registration with account activation
- JWT authentication (access + refresh)
- Password reset via email
- Password complexity enforcement
- Role-based access control:
  - **USER**
  - **MODERATOR**
  - **ADMIN**

### 🎥 Movies
- Movie catalog with pagination
- Search, filtering, sorting
- Genres, directors, actors
- Likes, comments, ratings
- Favorites list
- IMDb & metadata support

### 🛒 Shopping Cart
- One cart per user
- Prevent duplicate or already purchased movies
- Bulk checkout
- Cart validation before order creation

### 📦 Orders
- Pending / Paid / Canceled states
- Order history
- Order validation & re-calculation
- Email notifications

### 💳 Payments
- Stripe integration
- Payment history
- Refund support
- Secure webhook handling

### ⚙️ Admin & Moderator Tools
- Manage movies, genres, actors
- Manage users and roles
- View orders, carts, and payments
- Prevent deletion of purchased movies

---

## 🗂 Project Structure

```text
├── README.md
├── commands
├── docker
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs
│   └── dev-setup.md
├── poetry.lock
├── pyproject.toml
├── src
│   ├── alembic
│   ├── core
│   ├── db
│   ├── dependencies
│   ├── models
│   ├── schemas
│   └── services
└── tests
