from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

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
        SCHEDULED = 'scheduled', 'Scheduled'
        BOARDING = 'boarding', 'Boarding'
        DEPARTED = 'departed', 'Departed'
        DELAYED = 'delayed', 'Delayed'
        CANCELLED = 'cancelled', 'Cancelled'

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


class Order(models.Model):
    """
    Order for a flight ticket.
    Created when user wants to book a ticket.
    Reserves a seat for 15 minutes while waiting for payment confirmation.
    """
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Payment'
        PAID = 'paid', 'Paid'
        CONFIRMED = 'confirmed', 'Confirmed'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'

    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='orders')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    seat_number = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    reserved_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevent duplicate orders for the same seat when order is active
        constraints = [
            models.UniqueConstraint(
                fields=['flight', 'seat_number'],
                condition=models.Q(status__in=['pending', 'paid', 'confirmed']),
                name='unique_active_seat_per_flight'
            )
        ]

    def __str__(self):
        return f"Order {self.id} - {self.user.username} - Seat {self.seat_number} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-set reserved_until to 15 minutes from now if not set
        if not self.reserved_until:
            self.reserved_until = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if reservation has expired"""
        return timezone.now() > self.reserved_until and self.status == 'pending'


class Ticket(models.Model):
    """
    Actual ticket created after order is confirmed/paid.
    One ticket per order.
    """
    class TicketStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        USED = 'used', 'Used'
        CANCELLED = 'cancelled', 'Cancelled'

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='ticket')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='tickets')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    seat_number = models.CharField(max_length=10)
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.ACTIVE
    )

    class Meta:
        # Prevent duplicate tickets for the same seat on the same flight
        constraints = [
            models.UniqueConstraint(
                fields=['flight', 'seat_number'],
                name='unique_seat_per_flight'
            )
        ]

    def __str__(self):
        return f"Ticket {self.id} for {self.user.username} - Seat {self.seat_number}"