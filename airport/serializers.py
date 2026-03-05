from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction
from .models import Country, Airport, Airline, Airplane, Flight, Order, Ticket


# ============ Country Serializers ============

class CountrySerializer(serializers.ModelSerializer):
    """Basic country serializer"""
    airports_count = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = ('id', 'name', 'airports_count')

    def get_airports_count(self, obj):
        return obj.airports.count()


class CountryDetailSerializer(serializers.ModelSerializer):
    """Detailed country serializer with nested airports"""
    airports = serializers.SerializerMethodField()
    airports_count = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = ('id', 'name', 'airports_count', 'airports')

    def get_airports(self, obj):
        return AirportListSerializer(obj.airports.all(), many=True).data

    def get_airports_count(self, obj):
        return obj.airports.count()


# ============ Airport Serializers ============

class AirportListSerializer(serializers.ModelSerializer):
    """Short serializer for list view - basic info only"""
    country = serializers.StringRelatedField(read_only=True)
    country_details = CountrySerializer(source='country', read_only=True)

    class Meta:
        model = Airport
        fields = ('id', 'name', 'code', 'country', 'country_details')


class AirportDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail view - includes nested airlines"""
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source='country', write_only=True
    )
    airlines = serializers.SerializerMethodField()
    airlines_count = serializers.SerializerMethodField()

    class Meta:
        model = Airport
        fields = (
            'id', 'name', 'code', 'country', 'country_id',
            'airlines_count', 'airlines'
        )

    def get_airlines(self, obj):
        return AirlineSerializer(obj.airlines.all(), many=True).data

    def get_airlines_count(self, obj):
        return obj.airlines.count()


# ============ Airline Serializers ============

class AirlineSerializer(serializers.ModelSerializer):
    """Basic airline serializer"""
    airport_name = serializers.CharField(source='airport.name', read_only=True)
    airport_code = serializers.CharField(source='airport.code', read_only=True)

    class Meta:
        model = Airline
        fields = ('id', 'name', 'airport', 'airport_name', 'airport_code')


class AirlineDetailSerializer(serializers.ModelSerializer):
    """Full serializer with nested airport info and airplanes"""
    airport = AirportListSerializer(read_only=True)
    airport_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source='airport', write_only=True
    )
    airplanes = serializers.SerializerMethodField()
    airplanes_count = serializers.SerializerMethodField()

    class Meta:
        model = Airline
        fields = (
            'id', 'name', 'airport', 'airport_id',
            'airplanes_count', 'airplanes'
        )

    def get_airplanes(self, obj):
        return AirplaneSerializer(obj.airplanes.all(), many=True).data

    def get_airplanes_count(self, obj):
        return obj.airplanes.count()


# ============ Airplane Serializers ============

class AirplaneSerializer(serializers.ModelSerializer):
    """Basic airplane serializer"""
    airline_name = serializers.CharField(source='airline.name', read_only=True)

    class Meta:
        model = Airplane
        fields = ('id', 'name', 'capacity', 'airline', 'airline_name')


class AirplaneDetailSerializer(serializers.ModelSerializer):
    """Full serializer with nested airline and flights"""
    airline = AirlineSerializer(read_only=True)
    airline_id = serializers.PrimaryKeyRelatedField(
        queryset=Airline.objects.all(), source='airline', write_only=True
    )
    flights_count = serializers.SerializerMethodField()

    class Meta:
        model = Airplane
        fields = (
            'id', 'name', 'capacity', 'airline', 'airline_id',
            'flights_count'
        )

    def get_flights_count(self, obj):
        return obj.flights.count()


# ============ Flight Serializers ============

class FlightListSerializer(serializers.ModelSerializer):
    """Short serializer for list view - basic flight info"""
    airplane_name = serializers.CharField(source='airplane.name', read_only=True)
    airline_name = serializers.CharField(source='airplane.airline.name', read_only=True)
    tickets_sold = serializers.SerializerMethodField()
    tickets_available = serializers.SerializerMethodField()
    capacity = serializers.IntegerField(source='airplane.capacity', read_only=True)

    class Meta:
        model = Flight
        fields = (
            'id', 'number', 'airplane', 'airplane_name', 'airline_name',
            'departure_time', 'arrival_time', 'status', 'price',
            'capacity', 'tickets_sold', 'tickets_available'
        )

    def get_tickets_sold(self, obj):
        return obj.tickets.filter(status='active').count()

    def get_tickets_available(self, obj):
        from django.db.models import Q
        occupied = obj.tickets.filter(
            status__in=['reserved', 'active']
        ).count()
        return obj.airplane.capacity - occupied


class FlightDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail view - includes all related data"""
    airplane = AirplaneSerializer(read_only=True)
    airplane_id = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.all(), source='airplane', write_only=True
    )
    tickets_sold = serializers.SerializerMethodField()
    tickets_available = serializers.SerializerMethodField()
    capacity = serializers.IntegerField(source='airplane.capacity', read_only=True)
    airline = serializers.CharField(source='airplane.airline.name', read_only=True)
    tickets = serializers.SerializerMethodField()

    class Meta:
        model = Flight
        fields = (
            'id', 'number', 'airplane', 'airplane_id',
            'departure_time', 'arrival_time', 'status', 'price',
            'airline', 'capacity', 'tickets_sold', 'tickets_available',
            'tickets'
        )

    def get_tickets_sold(self, obj):
        return obj.tickets.filter(status='active').count()

    def get_tickets_available(self, obj):
        occupied = obj.tickets.filter(status__in=['reserved', 'active']).count()
        return obj.airplane.capacity - occupied

    def get_tickets(self, obj):
        return TicketSerializer(obj.tickets.filter(status='active'), many=True).data


# ============ Ticket Serializers ============

class TicketSerializer(serializers.ModelSerializer):
    """Basic ticket serializer"""
    flight_number = serializers.CharField(source='flight.number', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Ticket
        fields = (
            'id', 'flight', 'flight_number', 'user', 'username',
            'seat_number', 'price', 'status'
        )
        read_only_fields = ('user',)


class TicketDetailSerializer(serializers.ModelSerializer):
    """Full ticket serializer with complete flight and user details"""
    flight = FlightListSerializer(read_only=True)
    flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source='flight', write_only=True
    )
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = (
            'id', 'flight', 'flight_id', 'user', 'user_details',
            'seat_number', 'price', 'status'
        )
        read_only_fields = ('user',)

    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'is_airport_admin': obj.user.is_airport_admin
        }


# ============ Nested Ticket Input Serializer ============

class TicketInputSerializer(serializers.Serializer):
    """Used inside CreateOrderSerializer to accept a list of tickets.
    Price is optional — defaults to flight.price if not provided.
    """
    seat_number = serializers.CharField(max_length=10)
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False
    )

    def validate_seat_number(self, value):
        import re
        if not re.match(r'^\d+[A-F]$', value.upper()):
            raise ValidationError("Invalid seat format. Expected format: '1A', '12B', etc.")
        return value.upper()


# ============ Order Serializers ============

class CreateOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for creating an order with one or more tickets on the same flight.

    Input:
        {
            "flight_id": 1,
            "tickets": [
                {"seat_number": "1A", "price": 99.99},
                {"seat_number": "2B", "price": 149.99}
            ]
        }

    Output includes client_secret for Stripe.
    """
    flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source='flight', write_only=True
    )
    tickets = TicketInputSerializer(many=True, write_only=True)

    # Read-only output fields
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tickets_data = serializers.SerializerMethodField(read_only=True)
    client_secret = serializers.CharField(read_only=True)
    payment_intent_id = serializers.CharField(read_only=True)
    payment_status = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'flight_id', 'tickets', 'total_price',
            'status', 'reserved_until',
            'client_secret', 'payment_intent_id', 'payment_status',
            'tickets_data'
        )
        read_only_fields = ('id', 'status', 'reserved_until')

    def get_tickets_data(self, obj):
        return TicketSerializer(obj.tickets.all(), many=True).data

    def validate_tickets(self, value):
        if not value:
            raise ValidationError("At least one ticket is required.")
        if len(value) > 9:
            raise ValidationError("Maximum 9 tickets per order.")
        # Check for duplicate seats within the same request
        seats = [t['seat_number'] for t in value]
        if len(seats) != len(set(seats)):
            raise ValidationError("Duplicate seat numbers in the same order.")
        return value

    def validate(self, attrs):
        from django.utils import timezone
        from django.db.models import Q
        import re

        flight = attrs.get('flight')
        tickets_input = attrs.get('tickets', [])

        if not flight:
            raise ValidationError("Flight not found.")

        # Flight departure must be in the future
        if flight.departure_time <= timezone.now():
            raise ValidationError("Cannot book tickets for flights that have already departed.")

        # Flight must be bookable
        if flight.status not in ['scheduled', 'boarding']:
            raise ValidationError(f"Cannot book tickets for {flight.status} flights.")

        # Validate each seat
        max_rows = (flight.airplane.capacity + 5) // 6
        for item in tickets_input:
            seat = item['seat_number']
            match = re.match(r'^(\d+)[A-F]$', seat)
            if match:
                row = int(match.group(1))
                if row > max_rows or row < 1:
                    raise ValidationError(
                        f"Seat {seat} does not exist on this airplane "
                        f"(capacity: {flight.airplane.capacity}, max row: {max_rows})"
                    )

            # Check if seat is already taken
            if flight.tickets.filter(
                seat_number=seat,
                status__in=['reserved', 'active']
            ).exists():
                raise ValidationError(f"Seat {seat} is already reserved or booked on this flight.")

        # Check total capacity
        seats_requested = len(tickets_input)
        occupied = flight.tickets.filter(status__in=['reserved', 'active']).count()
        if occupied + seats_requested > flight.airplane.capacity:
            available = flight.airplane.capacity - occupied
            raise ValidationError(
                f"Not enough seats. Requested {seats_requested}, available {available}."
            )

        return attrs

    def create(self, validated_data):
        from django.db import IntegrityError
        from django.conf import settings as django_settings
        import stripe

        user = self.context['request'].user
        flight = validated_data['flight']
        tickets_input = validated_data['tickets']

        # Default ticket price to flight.price if not explicitly provided
        for t in tickets_input:
            if 'price' not in t or t['price'] is None:
                t['price'] = flight.price

        total_price = sum(t['price'] for t in tickets_input)

        try:
            with transaction.atomic():
                # Create the Order
                order = Order.objects.create(
                    user=user,
                    flight=flight,
                    total_price=total_price,
                )

                # Create all Tickets with status 'reserved'
                ticket_objs = [
                    Ticket(
                        order=order,
                        flight=flight,
                        user=user,
                        seat_number=t['seat_number'],
                        price=t['price'],
                        status=Ticket.TicketStatus.RESERVED,
                    )
                    for t in tickets_input
                ]
                Ticket.objects.bulk_create(ticket_objs)

                # Create Stripe Payment Intent
                if django_settings.STRIPE_SECRET_KEY:
                    try:
                        seat_list = ', '.join(t['seat_number'] for t in tickets_input)
                        payment_intent = stripe.PaymentIntent.create(
                            amount=int(total_price * 100),  # cents
                            currency='usd',
                            metadata={
                                'order_id': order.id,
                                'user_id': user.id,
                                'user_email': user.email,
                                'flight_number': flight.number,
                                'seats': seat_list,
                                'ticket_count': len(tickets_input),
                            },
                            automatic_payment_methods={
                                'enabled': True,
                                'allow_redirects': 'never'
                            }
                        )
                        order.payment_intent_id = payment_intent.id
                        order.payment_status = payment_intent.status
                        order.save()
                        order.client_secret = payment_intent.client_secret
                    except stripe.error.StripeError as e:
                        print(f"⚠️ Stripe Payment Intent creation failed: {e}")
                        order.client_secret = None
                else:
                    order.client_secret = None

                return order

        except IntegrityError as e:
            if 'unique_active_seat_per_flight' in str(e):
                raise ValidationError(
                    "One or more seats were just booked by another user. Please try different seats."
                )
            raise


class OrderListSerializer(serializers.ModelSerializer):
    """Basic order serializer for list view"""
    flight_number = serializers.CharField(source='flight.number', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    ticket_count = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    time_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'flight', 'flight_number', 'user', 'username',
            'total_price', 'ticket_count', 'status', 'reserved_until',
            'is_expired', 'time_until_expiry',
            'payment_intent_id', 'payment_status', 'created_at'
        )

    def get_ticket_count(self, obj):
        return obj.tickets.count()

    def get_is_expired(self, obj):
        return obj.is_expired()

    def get_time_until_expiry(self, obj):
        from django.utils import timezone
        if obj.status == 'pending':
            delta = obj.reserved_until - timezone.now()
            if delta.total_seconds() > 0:
                return f"{int(delta.total_seconds() // 60)} minutes"
        return None


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full order serializer with nested flight, tickets, and user details"""
    flight = FlightListSerializer(read_only=True)
    user_details = serializers.SerializerMethodField()
    tickets = TicketSerializer(many=True, read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'flight', 'user', 'user_details',
            'total_price', 'status', 'reserved_until', 'is_expired',
            'payment_intent_id', 'payment_status',
            'tickets', 'created_at', 'updated_at'
        )

    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
        }

    def get_is_expired(self, obj):
        return obj.is_expired()