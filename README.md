# ✈️ Airport API

REST API для системи управління аеропортом — бронювання квитків, управління рейсами, літаками та авіалініями.

## 🛠 Технології

- **Python 3.12+**
- **Django 5.2** + **Django REST Framework**
- **PostgreSQL** — база даних
- **JWT** (Simple JWT) — авторизація
- **drf-spectacular** — автогенерація OpenAPI документації

## 📦 Встановлення

```bash
# Клонування репозиторію
git clone https://github.com/your-username/airport_project.git
cd airport_project

# Створення віртуального середовища
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Встановлення залежностей
pip install -r requirements.txt

# Налаштування бази даних (PostgreSQL)
# Створіть базу даних 'airport_db' та оновіть credentials в settings.py

# Застосування міграцій
python manage.py migrate

# Створення суперкористувача
python manage.py createsuperuser

# Запуск сервера
python manage.py runserver
```

## 📊 Моделі даних

```
Country (Країна)
    └── Airport (Аеропорт)
            └── Airline (Авіалінія)
                    └── Airplane (Літак)
                            └── Flight (Рейс)
                                    └── Ticket (Квиток) ← User (Користувач)
```

| Модель | Поля |
|--------|------|
| `User` | username, email, password, is_airport_admin |
| `Country` | name |
| `Airport` | name, code, country |
| `Airline` | name, airport |
| `Airplane` | name, capacity, airline |
| `Flight` | number, airplane, departure_time, arrival_time, status |
| `Ticket` | flight, user, seat_number, status |

### Статуси рейсів
- `scheduled` — Запланований
- `boarding` — Посадка
- `departed` — Вилетів
- `delayed` — Затриманий
- `cancelled` — Відмінений

### Статуси квитків
- `booked` — Заброньований
- `paid` — Оплачений
- `used` — Використаний
- `cancelled` — Скасований

## 🔗 API Ендпоінти

### Авторизація
| Метод | URL | Опис |
|-------|-----|------|
| POST | `/api/token/` | Отримати JWT токени |
| POST | `/api/token/refresh/` | Оновити access токен |

### Ресурси
| Ресурс | URL | Методи |
|--------|-----|--------|
| Countries | `/api/countries/` | GET, POST, PUT, DELETE |
| Airports | `/api/airports/` | GET, POST, PUT, DELETE |
| Airlines | `/api/airlines/` | GET, POST, PUT, DELETE |
| Airplanes | `/api/airplanes/` | GET, POST, PUT, DELETE |
| Flights | `/api/flights/` | GET, POST*, PUT*, DELETE* |
| Tickets | `/api/tickets/` | GET**, POST**, PUT**, DELETE** |

\* — тільки для адміністраторів  
\** — потребує авторизації, користувач бачить тільки свої квитки

### Документація
- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/

## 🔐 Авторизація

Проєкт використовує JWT токени. Приклад використання:

```bash
# Отримання токенів
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_user", "password": "your_password"}'

# Використання токена
curl http://127.0.0.1:8000/api/tickets/ \
  -H "Authorization: Bearer <your_access_token>"
```

## 🔒 Права доступу

| Ресурс | Читання | Запис |
|--------|---------|-------|
| Countries, Airports, Airlines, Airplanes | Всі | Всі |
| Flights | Всі | Тільки адміни |
| Tickets | Авторизовані (свої) | Авторизовані (свої) |

**Важливо**: Одне місце на рейсі може бути заброньоване тільки один раз (унікальне обмеження `flight` + `seat_number`).

## 📁 Структура проєкту

```
airport_project/
├── airport/                 # Основний додаток
│   ├── models.py           # Моделі даних
│   ├── views.py            # ViewSets для API
│   ├── serializers.py      # Серіалізатори
│   ├── urls.py             # Роутінг API
│   ├── permission.py       # Кастомні права доступу
│   └── admin.py            # Конфігурація адмін-панелі
├── airport_config/          # Конфігурація Django
│   ├── settings.py         # Налаштування проєкту
│   ├── urls.py             # Головний роутінг
│   └── wsgi.py / asgi.py   # WSGI/ASGI конфігурація
├── manage.py
├── requirements.txt
└── README.md
```

## 🧪 Тестування

```bash
python manage.py test
```

## 📝 Ліцензія

MIT License
