from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_airport_admin = models.BooleanField(default=False)
    
    @property
    def is_admin(self):
        return self.is_staff or self.is_airport_admin

class Country(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
    
class Airport(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='airports')

    def __str__(self):
        return f"{self.name}, ({self.code})"

class Airline(models.Model):
    name = models.CharField(max_length=255)
    airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='airlines')

    def __str__(self):
        return self.name
    
class Airplane(models.Model):
    name = models.CharField(max_length=255)
    capacity = models.IntegerField()
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name='airplanes')

    def __str__(self):
        return f"{self.name} (Cap: {self.capacity})"
    
class Flight(models.Model):
    class FlightStatus(models.TextChoices):
        SCHEDULED = 'scheduled', 'Запланований'
        BOARDING = 'boarding', 'Посадка'
        DEPARTED = 'departed', 'Вилетів'
        DELAYED = 'delayed', 'Затриманий'
        CANCELLED = 'cancelled', 'Відмінений'

    number = models.CharField(max_length=50, unique=True)
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name='flights')
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices=FlightStatus.choices, 
        default=FlightStatus.SCHEDULED
    )

    def __str__(self):
        return f"Flight {self.number} - {self.status}"
    
class Ticket(models.Model):
    class TicketStatus(models.TextChoices):
        BOOKED = 'booked', 'Заброньований'
        CANCELLED = 'cancelled', 'Скасований'
        USED = 'used', 'Використаний'
        PAID = 'paid', 'Оплачений'

    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='tickets')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    seat_number = models.CharField(max_length=10)
    status = models.CharField(
        max_length=20, 
        choices=TicketStatus.choices, 
        default=TicketStatus.BOOKED
    )

    class Meta:
        # Забороняємо два квитки на одне й те саме місце на одному рейсі
        constraints = [
            models.UniqueConstraint(
                fields=['flight', 'seat_number'],
                name='unique_seat_per_flight'
            )
        ]

    def __str__(self):
        return f"Ticket {self.id} for {self.user.username}"