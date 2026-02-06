# ✈️ Airport API

REST API for airport management system — ticket booking, flight management, airplanes, and airlines.

## 🛠 Technologies

- **Python 3.12+**
- **Django 5.2** + **Django REST Framework**
- **PostgreSQL** — database
- **JWT** (Simple JWT) — authorization
- **drf-spectacular** — OpenAPI documentation auto-generation

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/your-username/airport_project.git
cd airport_project

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure database (PostgreSQL)
# Create database 'airport_db' and update credentials in settings.py

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## 📊 Data Models

```
Country
    └── Airport
            └── Airline
                    └── Airplane
                            └── Flight
                                    └── Ticket ← User
```

| Model | Fields |
|--------|---------|
| `User` | username, email, password, is_airport_admin |
| `Country` | name |
| `Airport` | name, code, country |
| `Airline` | name, airport |
| `Airplane` | name, capacity, airline |
| `Flight` | number, airplane, departure_time, arrival_time, status |
| `Ticket` | flight, user, seat_number, status |

### Flight Statuses
- `scheduled` — Scheduled
- `boarding` — Boarding
- `departed` — Departed
- `delayed` — Delayed
- `cancelled` — Cancelled

### Ticket Statuses
- `booked` — Booked
- `paid` — Paid
- `used` — Used
- `cancelled` — Cancelled

## 🔗 API Endpoints

### Authorization
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/token/` | Get JWT tokens |
| POST | `/api/token/refresh/` | Refresh access token |

### Resources
| Resource | URL | Methods |
|----------|-----|---------|
| Countries | `/api/countries/` | GET, POST, PUT, DELETE |
| Airports | `/api/airports/` | GET, POST, PUT, DELETE |
| Airlines | `/api/airlines/` | GET, POST, PUT, DELETE |
| Airplanes | `/api/airplanes/` | GET, POST, PUT, DELETE |
| Flights | `/api/flights/` | GET, POST*, PUT*, DELETE* |
| Tickets | `/api/tickets/` | GET**, POST**, PUT**, DELETE** |

\* — admin only  
\** — requires authorization, users can only see their own tickets

### Documentation
- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/

## 🔐 Authorization

The project uses JWT tokens. Usage example:

```bash
# Get tokens
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_user", "password": "your_password"}'

# Use token
curl http://127.0.0.1:8000/api/tickets/ \
  -H "Authorization: Bearer <your_access_token>"
```

## 🔒 Access Rights

| Resource | Read | Write |
|----------|------|-------|
| Countries, Airports, Airlines, Airplanes | All | All |
| Flights | All | Admin only |
| Tickets | Authorized (own) | Authorized (own) |

**Important**: Each seat on a flight can only be booked once (unique constraint on `flight` + `seat_number`).

## 📁 Project Structure

```
airport_project/
├── airport/                 # Main application
│   ├── models.py           # Data models
│   ├── views.py            # API ViewSets
│   ├── serializers.py      # Serializers
│   ├── urls.py             # API routing
│   ├── permission.py       # Custom permissions
│   └── admin.py            # Admin panel configuration
├── airport_config/          # Django configuration
│   ├── settings.py         # Project settings
│   ├── urls.py             # Main routing
│   └── wsgi.py / asgi.py   # WSGI/ASGI configuration
├── manage.py
├── requirements.txt
└── README.md
```

## 🧪 Testing

```bash
python manage.py test
```
