# Fahari Grand Hotel & Suites - Backend

## A. Contributor

* **Albert Junior Quarshie**

---

## B. Overview

* **Fahari Grand Hotel & Suites** is a hotel and accommodation booking system backend built using Django and Django REST Framework, serving a Nairobi-based hotel.

* The system supports four distinct user roles — Guest, Receptionist, Admin, and Housekeeper — each with permissions tailored to their responsibilities within the hotel's operations.

* Guests can browse available rooms, make bookings, and pay via M-Pesa. Receptionists manage check-ins/check-outs and walk-in bookings. Housekeeping staff track room status and cleaning tasks. Admins oversee rooms, staff, pricing, and reporting.

---

## C. Requirements

The following software should be installed before running the project:

1. Python 3.14.4

2. Django (Latest Version)

3. PostgreSQL

4. Ngrok (for testing M-Pesa Transactions)

5. Postman (for testing the endpoints)

---

## D. Installation

### 1. Clone the Repository

```bash
git clone https://github.com/AlbertQuarshie/fahari-backend.git
cd fahari-backend
```

### 2. Create a Virtual Environment

```bash
# Windows
python -m venv my_env
my_env\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and set the following:

```bash
SECRET_KEY=your_django_secret_key

DB_NAME=fahari_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

MPESA_SECRET_KEY=your_Mpesa_secret_key_of_your_sandbox_app
MPESA_CONSUMER_SECRET=your_Mpesa_consumer_secret_of_your_sandbox_app
MPESA_SHORTCODE=174379  # This is default across all sandbox apps
MPESA_PASSKEY=Your_Mpesa_passkey_of_your_sandbox_app
MPESA_CALLBACK_URL=YOUR_MPESA_CALLBACK_URL_of_your_sandbox_app

CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret


```

- Note: This project is configured for PostgreSQL by default. Update `settings.py` if a different database is required.

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a Superuser

```bash
python manage.py createsuperuser
```

### 7. Start the Server

```bash
python manage.py runserver
```

---

## E. Usage

### 1. User Registration

* Guests can register for an account to make bookings; staff accounts are created by the Admin.

### 2. Login

* Sign in using registered credentials. Role-based access determines available actions.

### 3. Browse Rooms

* View available rooms, filter by date, room type, and price.

### 4. Make a Booking

* Reserve a room for selected check-in and check-out dates.

### 5. Make Payment

* Pay for a booking via M-Pesa or card through Paystack.

### 6. Manage Stay (Staff)

* Receptionists handle check-in/check-out; Housekeeping updates room cleaning status; Admins manage rooms, rates, and staff.

---

## F. Features

### 1. User Authentication & Role-Based Access

* Secure registration and login system.
* Four roles: Guest, Receptionist, Admin, Housekeeper, each with scoped permissions.
* Passwords stored using hashing.

### 2. Room Management

* Create, update, and remove room listings.
* Track room availability and status (available, occupied, cleaning, maintenance).

### 3. Booking Management

* Create, view, modify, and cancel bookings.
* Automatic availability checks to prevent double-booking.

### 4. Payments

* Integrated with M-pesa Daraja Api which is provided directly by Safaricom
* Payment status tracking linked to bookings.

### 5. Check-In / Check-Out

* Receptionist tools to process guest arrivals and departures.

### 6. Housekeeping

* Task assignment and room status updates for cleaning staff.

### 7. Admin Dashboard

* Manage staff accounts, room inventory, pricing, and view booking/revenue reports.

---

## G. API Endpoints

### Authentication Endpoints

```http
POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/logout/
```

### Room Endpoints

```http
GET    /api/rooms/
GET    /api/rooms/{room_id}/
POST   /api/rooms/
PUT    /api/rooms/{room_id}/
DELETE /api/rooms/{room_id}/
```

### Booking Endpoints

```http
GET    /api/bookings/
GET    /api/bookings/{booking_id}/
POST   /api/bookings/
PUT    /api/bookings/{booking_id}/
DELETE /api/bookings/{booking_id}/
```

### Payment Endpoints

```http
POST   /api/payments/initiate/
POST   /api/payments/verify/
GET    /api/payments/{payment_id}/
```

### Check-In / Check-Out Endpoints

```http
POST   /api/bookings/{booking_id}/checkin/
POST   /api/bookings/{booking_id}/checkout/
```

### Housekeeping Endpoints

```http
GET    /api/housekeeping/tasks/
PUT    /api/housekeeping/tasks/{task_id}/
```

### Admin Endpoints

```http
GET    /api/admin/staff/
POST   /api/admin/staff/
GET    /api/admin/reports/
```

---

## H. Tech Stack

| Layer                | Technology                  |
| -------------------- | ----------------------------|
| Programming Language | Python                      |
| Framework            | Django                      |
| API Framework        | Django REST Framework       |
| Database             | PostgreSQL                  |
| Authentication       | Simple JWT       |
| Payments             | Mpesa Daraja API            |
| Deployment           | Render                      |

---

## I. Screenshots

1. Login Page Endpoint
![Login](screenshots/image-1.png)

2. Room Listing Endpoint
![Rooms](screenshots/image-2.png)

3. Booking Endpoint
![Bookings](screenshots/image.png)
