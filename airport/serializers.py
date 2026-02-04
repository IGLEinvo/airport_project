from rest_framework import serializers
from .models import Country, Airport, Airline, Airplane, Flight, Ticket, User

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name')

class AirportSerializer(serializers.ModelSerializer):
    # Використовуємо StringRelatedField, щоб бачити назву країни, а не ID
    country = serializers.StringRelatedField(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source='country', write_only=True
    )

    class Meta:
        model = Airport
        fields = ('id', 'name', 'code', 'country', 'country_id')

class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ('id', 'name', 'airport')

class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ('id', 'name', 'capacity', 'airline')

class FlightSerializer(serializers.ModelSerializer):
    # Можна додати обчислювальне поле: скільки вільних місць залишилось
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = (
            'id', 'number', 'airplane', 'departure_time', 
            'arrival_time', 'status', 'tickets_available'
        )

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ('id', 'flight', 'user', 'seat_number', 'status')
        read_only_fields = ('user',) # Юзера будемо брати з запиту (request.user)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'is_airport_admin')
        extra_kwargs = {'password': {'write_only': True}}