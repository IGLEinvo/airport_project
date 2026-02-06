from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Country, Airport, Airline, Airplane, Flight, Ticket
from .permission import IsAdminOrReadOnly
from .serializers import (
    CountrySerializer, 
    AirportListSerializer, AirportDetailSerializer,
    AirlineSerializer, AirlineDetailSerializer,
    AirplaneSerializer, 
    FlightListSerializer, FlightDetailSerializer,
    TicketSerializer, TicketDetailSerializer
)


# ============ GenericAPIView examples for Country ============

class CountryListCreateView(generics.GenericAPIView):
    """
    GET: List all countries
    POST: Create a new country
    """
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    def get(self, request):
        countries = self.get_queryset()
        serializer = self.get_serializer(countries, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CountryDetailView(generics.GenericAPIView):
    """
    GET: Retrieve a country
    PUT: Update a country
    DELETE: Delete a country
    """
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    def get_object(self):
        pk = self.kwargs.get('pk')
        return generics.get_object_or_404(self.get_queryset(), pk=pk)

    def get(self, request, pk):
        country = self.get_object()
        serializer = self.get_serializer(country)
        return Response(serializer.data)

    def put(self, request, pk):
        country = self.get_object()
        serializer = self.get_serializer(country, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        country = self.get_object()
        country.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============ Airport ViewSet with multiple serializers ============

class AirportViewSet(viewsets.ModelViewSet):
    """
    Uses AirportListSerializer for list action (basic info)
    Uses AirportDetailSerializer for retrieve/create/update (full info with airlines)
    """
    queryset = Airport.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return AirportListSerializer
        return AirportDetailSerializer


class AirlineViewSet(viewsets.ModelViewSet):
    queryset = Airline.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return AirlineSerializer
        return AirlineDetailSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer


# ============ Flight ViewSet with multiple serializers ============

class FlightViewSet(viewsets.ModelViewSet):
    """
    Uses FlightListSerializer for list action (basic flight info)
    Uses FlightDetailSerializer for retrieve (full info with tickets)
    """
    queryset = Flight.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return FlightListSerializer
        return FlightDetailSerializer


# ============ Ticket ViewSet with multiple serializers ============

class TicketViewSet(viewsets.ModelViewSet):
    """
    Uses TicketSerializer for list action
    Uses TicketDetailSerializer for retrieve (includes flight details)
    """
    queryset = Ticket.objects.all()
    authentication_classes = [JWTAuthentication] 
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return TicketSerializer
        return TicketDetailSerializer

    def perform_create(self, serializer):
        # User ID is taken from token, not provided by the user
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # Admin sees all tickets, regular users only see their own
        if self.request.user.is_staff:
            return Ticket.objects.all()
        return Ticket.objects.filter(user=self.request.user)