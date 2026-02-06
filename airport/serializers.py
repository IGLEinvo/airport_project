from rest_framework import serializers
from .models import Country, Airport, Airline, Airplane, Flight, Ticket


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name')


# ============ Airport Serializers ============

class AirportListSerializer(serializers.ModelSerializer):
    """Short serializer for list view - basic info only"""
    country = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Airport
        fields = ('id', 'name', 'code', 'country')


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
    class Meta:
        model = Airline
        fields = ('id', 'name', 'airport')


class AirlineDetailSerializer(serializers.ModelSerializer):
    """Full serializer with nested airport info"""
    airport = AirportListSerializer(read_only=True)
    airport_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source='airport', write_only=True
    )

    class Meta:
        model = Airline
        fields = ('id', 'name', 'airport', 'airport_id')


# ============ Airplane Serializer ============

class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ('id', 'name', 'capacity', 'airline')


# ============ Flight Serializers ============

class FlightListSerializer(serializers.ModelSerializer):
    """Short serializer for list view - basic flight info"""
    airplane_name = serializers.CharField(source='airplane.name', read_only=True)
    tickets_sold = serializers.SerializerMethodField()

    class Meta:
        model = Flight
        fields = (
            'id', 'number', 'airplane', 'airplane_name',
            'departure_time', 'arrival_time', 'status', 'tickets_sold'
        )

    def get_tickets_sold(self, obj):
        return obj.tickets.count()


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
        return obj.tickets.count()

    def get_tickets_available(self, obj):
        return obj.airplane.capacity - obj.tickets.count()

    def get_tickets(self, obj):
        return TicketSerializer(obj.tickets.all(), many=True).data


# ============ Ticket Serializers ============

class TicketSerializer(serializers.ModelSerializer):
    """Basic ticket serializer"""
    class Meta:
        model = Ticket
        fields = ('id', 'flight', 'user', 'seat_number', 'status')
        read_only_fields = ('user',)


class TicketDetailSerializer(serializers.ModelSerializer):
    """Full ticket serializer with flight details"""
    flight = FlightListSerializer(read_only=True)
    flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source='flight', write_only=True
    )
    user_email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Ticket
        fields = (
            'id', 'flight', 'flight_id', 'user', 'username', 'user_email',
            'seat_number', 'status'
        )
        read_only_fields = ('user',)