# 🚗 RenPark - Rental Car Parking Management System

RenPark is a web-based application built using Django (Python) that simplifies the rental and management of parking slots. It allows users to register as **Tenants** or **Landlords**, book or rent out parking spots, and manage all parking activities with ease.

---

## 🔥 Features

### 👤 User Module
- User Registration & Login (Single page toggle system)
- Role Selection: Tenant or Landlord
- Profile management
- View booking history

### 🅿️ Parking Slot Module
- Add, view, and manage parking slots
- Real-time slot availability status
- Slot details with pricing and location

### 📅 Booking Module
- Reserve parking slots for specific date/time
- View booking confirmation with timing and slot ID
- Cancel bookings before reservation time

### 🛠️ Admin Module
- Dashboard to manage users and bookings
- Slot creation, updating, and deletion
- View all bookings and revenue tracking

### 💳 Payment Module (Optional)
- Calculate rental fee based on duration
- Online payment integration (coming soon)
- Generate digital invoices

---

## 🧰 Tech Stack

| Layer       | Technology            |
|-------------|------------------------|
| Backend     | Python, Django         |
| Frontend    | HTML, CSS, JavaScript  |
| Database    | SQLite          |
| Editor      | VS Code       |

---

## 🖥️ System Requirements

### 🧑‍💻 Software
- Python 3.9+
- Django 4+
- SQLite (default) or MySQL
- Chrome / Firefox browser

### 💻 Hardware
- Dual Core processor or higher
- 2GB RAM minimum
- 500MB free disk space
- Basic internet connection

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/denmarkdeni/RenPark.git
cd RenPark

```

### 2. Virtual Environment

- install latest python version
- compress the project folder
- extract and delete env folder
- type cmd in project folder address box
- python -m venv env  --- to install env folder
- env\Scripts\activate  --- to activate env folder
- pip install -r requirements.txt -- to install all packages
- python manage.py makemigrations
- python manage.py migrate
- python manage.py runserver

- python manage.py createsuperuser


