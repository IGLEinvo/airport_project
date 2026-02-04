from rest_framework import viewsets, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Country, Airport, Airline, Airplane, Flight, Ticket
from .permission import IsAdminOrReadOnly
from .serializers import (
    CountrySerializer, AirportSerializer, AirlineSerializer, 
    AirplaneSerializer, FlightSerializer, TicketSerializer
)

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

class AirlineViewSet(viewsets.ModelViewSet):
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer

class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    # Примусово вказуємо, як перевіряти користувача
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrReadOnly]

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    authentication_classes = [JWTAuthentication] # Додаємо сюди теж
    permission_classes = [permissions.IsAuthenticated] # Тільки залогінені

    def perform_create(self, serializer):
        # Користувач не вказує свій ID сам, ми беремо його з токена
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # Адмін бачить все, юзер - тільки свої квитки
        if self.request.user.is_staff:
            return Ticket.objects.all()
        return Ticket.objects.filter(user=self.request.user)