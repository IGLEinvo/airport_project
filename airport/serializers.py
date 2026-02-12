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
        from .serializers import AirportListSerializer
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

    class Meta:
        model = Flight
        fields = (
            'id', 'number', 'airplane', 'airplane_name', 'airline_name',
            'departure_time', 'arrival_time', 'status', 
            'tickets_sold', 'tickets_available'
        )

    def get_tickets_sold(self, obj):
        """Count of confirmed tickets"""
        return obj.tickets.count()
    
    def get_tickets_available(self, obj):
        """Available seats accounting for both tickets and active orders"""
        from django.utils import timezone
        from django.db.models import Q
        
        # Count confirmed tickets
        total_tickets = obj.tickets.count()
        
        # Count active orders WITHOUT tickets (to avoid double counting):
        # - paid/confirmed orders that don't have a ticket yet
        # - pending with valid reservation (reserved_until > now)
        active_orders_without_tickets = obj.orders.filter(
            Q(status__in=['paid', 'confirmed'], ticket__isnull=True) |  # Orders without tickets
            Q(status='pending', reserved_until__gt=timezone.now())
        ).count()
        
        total_occupied = total_tickets + active_orders_without_tickets
        return obj.airplane.capacity - total_occupied


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
            'departure_time', 'arrival_time', 'status',
            'airline', 'capacity', 'tickets_sold', 'tickets_available',
            'tickets'
        )

    def get_tickets_sold(self, obj):
        """Count of confirmed tickets"""
        return obj.tickets.count()

    def get_tickets_available(self, obj):
        """Available seats accounting for both tickets and active orders"""
        from django.utils import timezone
        from django.db.models import Q
        
        # Count confirmed tickets
        total_tickets = obj.tickets.count()
        
        # Count active orders WITHOUT tickets (to avoid double counting):
        # - paid/confirmed orders that don't have a ticket yet
        # - pending with valid reservation (reserved_until > now)
        active_orders_without_tickets = obj.orders.filter(
            Q(status__in=['paid', 'confirmed'], ticket__isnull=True) |  # Orders without tickets
            Q(status='pending', reserved_until__gt=timezone.now())
        ).count()
        
        total_occupied = total_tickets + active_orders_without_tickets
        return obj.airplane.capacity - total_occupied

    def get_tickets(self, obj):
        return TicketSerializer(obj.tickets.all(), many=True).data


# ============ Order Serializers ============

class CreateOrderSerializer(serializers.ModelSerializer):
    """Serializer for creating an order (booking a seat on a flight)"""
    flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source='flight', write_only=True
    )
    
    class Meta:
        model = Order
        fields = ('flight_id', 'seat_number', 'price')
        
    def validate_seat_number(self, value):
        """Validate seat format (e.g., 1A, 12B, etc.)"""
        if not value:
            raise ValidationError("Seat number is required")
        
        # Basic validation: should have number + letter
        import re
        if not re.match(r'^\d+[A-F]$', value.upper()):
            raise ValidationError(
                "Invalid seat format. Expected format: '1A', '12B', etc."
            )
        return value.upper()
    
    def validate(self, attrs):
        """Check if seat is available and flight is bookable"""
        from django.utils import timezone
        from django.db.models import Q
        
        flight = attrs.get('flight')
        seat_number = attrs['seat_number']
        
        if not flight:
            raise ValidationError("Flight not found")
        
        # ✅ FIX #1: Check if flight departure is in the future
        if flight.departure_time <= timezone.now():
            raise ValidationError(
                "Cannot book tickets for flights that have already departed"
            )
        
        # Check if flight is bookable
        if flight.status not in ['scheduled', 'boarding']:
            raise ValidationError(
                f"Cannot book tickets for {flight.status} flights"
            )
        
        # ✅ FIX #2: Validate seat_number against airplane capacity
        # Extract row number from seat (e.g., "25A" -> 25)
        import re
        match = re.match(r'^(\d+)[A-F]$', seat_number)
        if match:
            row_number = int(match.group(1))
            # Assuming 6 seats per row (A-F), check if row exists
            max_rows = (flight.airplane.capacity + 5) // 6  # Round up
            if row_number > max_rows or row_number < 1:
                raise ValidationError(
                    f"Seat {seat_number} does not exist on this airplane (capacity: {flight.airplane.capacity}, max row: {max_rows})"
                )
        
        # Check if seat is already taken by a confirmed ticket
        if flight.tickets.filter(seat_number=seat_number).exists():
            raise ValidationError(
                f"Seat {seat_number} is already booked on this flight"
            )
        
        # ✅ FIX #4: Optimized check for active orders (single query)
        # Check if seat is reserved by active order (paid/confirmed OR pending non-expired)
        conflicting_orders = flight.orders.filter(
            seat_number=seat_number
        ).filter(
            Q(status__in=['paid', 'confirmed']) |  # These are always active
            Q(status='pending', reserved_until__gt=timezone.now())  # Pending but not expired
        )
        
        if conflicting_orders.exists():
            order = conflicting_orders.first()
            if order.status in ['paid', 'confirmed']:
                raise ValidationError(
                    f"Seat {seat_number} is already booked on this flight"
                )
            else:  # pending
                time_left = (order.reserved_until - timezone.now()).seconds // 60
                raise ValidationError(
                    f"Seat {seat_number} is currently reserved (expires in {time_left} minutes)"
                )
        
        # ✅ FIX #4: Check if flight is full (corrected logic - no double counting)
        # Count confirmed tickets
        total_tickets = flight.tickets.count()
        
        # Count active orders WITHOUT tickets:
        # - paid/confirmed (without ticket to avoid double count)
        # - pending with valid reservation
        active_orders_without_tickets = flight.orders.filter(
            Q(status__in=['paid', 'confirmed'], ticket__isnull=True) |
            Q(status='pending', reserved_until__gt=timezone.now())
        ).count()
        
        total_occupied = total_tickets + active_orders_without_tickets
        
        if total_occupied >= flight.airplane.capacity:
            raise ValidationError(
                f"Flight is fully booked ({total_occupied}/{flight.airplane.capacity} seats occupied)"
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create order with auto-calculated reserved_until"""
        from django.db import transaction, IntegrityError
        
        user = self.context['request'].user
        
        # ✅ FIX #3: Wrap in transaction.atomic and handle race conditions
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    **validated_data
                )
                return order
        except IntegrityError as e:
            # Race condition: another user booked the same seat between validate() and create()
            if 'unique_active_seat_per_flight' in str(e):
                raise ValidationError(
                    f"Seat {validated_data['seat_number']} was just booked by another user. Please try a different seat."
                )
            raise  # Re-raise other IntegrityErrors


class OrderListSerializer(serializers.ModelSerializer):
    """Basic order serializer for list view"""
    flight_number = serializers.CharField(source='flight.number', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    is_expired = serializers.SerializerMethodField()
    time_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = (
            'id', 'flight', 'flight_number', 'user', 'username',
            'seat_number', 'price', 'status', 'reserved_until',
            'is_expired', 'time_until_expiry', 'created_at'
        )
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_time_until_expiry(self, obj):
        """Return minutes until expiry, or None if already expired"""
        from django.utils import timezone
        if obj.status == 'pending':
            delta = obj.reserved_until - timezone.now()
            if delta.total_seconds() > 0:
                return f"{int(delta.total_seconds() // 60)} minutes"
        return None


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full order serializer with nested flight and user details"""
    flight = FlightListSerializer(read_only=True)
    user_details = serializers.SerializerMethodField()
    ticket = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = (
            'id', 'flight', 'user', 'user_details', 'seat_number',
            'price', 'status', 'reserved_until', 'is_expired',
            'ticket', 'created_at', 'updated_at'
        )
    
    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
        }
    
    def get_ticket(self, obj):
        """Return ticket details if order has a ticket"""
        if hasattr(obj, 'ticket'):
            from .serializers import TicketSerializer
            return TicketSerializer(obj.ticket).data
        return None
    
    def get_is_expired(self, obj):
        return obj.is_expired()


# ============ Ticket Serializers ============

class TicketSerializer(serializers.ModelSerializer):
    """Basic ticket serializer with nested info"""
    flight_number = serializers.CharField(source='flight.number', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Ticket
        fields = (
            'id', 'flight', 'flight_number', 'user', 'username',
            'seat_number', 'status'
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
            'seat_number', 'status'
        )
        read_only_fields = ('user',)
    
    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'is_airport_admin': obj.user.is_airport_admin
        }