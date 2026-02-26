from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Country, Airport, Airline, Airplane, Flight, Order, Ticket
from .permission import IsAdminOrReadOnly
from .serializers import (
    CountrySerializer, CountryDetailSerializer,
    AirportListSerializer, AirportDetailSerializer,
    AirlineSerializer, AirlineDetailSerializer,
    AirplaneSerializer, AirplaneDetailSerializer,
    FlightListSerializer, FlightDetailSerializer,
    TicketSerializer, TicketDetailSerializer,
    CreateOrderSerializer, OrderListSerializer, OrderDetailSerializer
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
    GET: Retrieve a country with nested airports
    PUT: Update a country
    DELETE: Delete a country
    """
    queryset = Country.objects.all()
    serializer_class = CountryDetailSerializer

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

    def get_serializer_class(self):
        if self.action == 'list':
            return AirplaneSerializer
        return AirplaneDetailSerializer


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


# ============ Order ViewSet ============

class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders (ticket bookings).
    Users can create orders, view their orders, confirm payment, and cancel orders.
    """
    queryset = Order.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return CreateOrderSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        # Admin sees all orders, regular users only see their own
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # User is read from context['request'].user inside CreateOrderSerializer.create()
        serializer.save()


    @action(
        detail=True,
        methods=['patch'],
        url_path='confirm'
    )
    def confirm_payment(self, request, pk=None):
        """
        Confirm payment for an order.
        Creates a Ticket and changes Order status to 'confirmed'.
        
        PATCH /api/orders/{id}/confirm/
        """
        from django.utils import timezone
        from django.db import transaction
        
        order = self.get_object()
        
        # Validation
        if order.status != 'pending':
            return Response(
                {'error': f'Cannot confirm order with status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if timezone.now() > order.reserved_until:
            order.status = 'expired'
            order.save()
            return Response(
                {'error': 'Order reservation has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Transaction to ensure atomicity
        with transaction.atomic():
            order.status = 'confirmed'
            order.save()
            
            ticket = Ticket.objects.create(
                order=order,
                flight=order.flight,
                user=order.user,
                seat_number=order.seat_number,
                status='active'
            )
        
        return Response(
            {
                'message': 'Payment confirmed successfully',
                'order': OrderDetailSerializer(order).data,
                'ticket': TicketDetailSerializer(ticket).data
            },
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='cancel'
    )
    def cancel_order(self, request, pk=None):
        """
        Cancel an order (releases the reserved seat).
        
        POST /api/orders/{id}/cancel/
        """
        order = self.get_object()
        
        if order.status not in ['pending', 'paid']:
            return Response(
                {'error': f'Cannot cancel order with status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.save()
        
        return Response(
            {'message': 'Order cancelled successfully'},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='checkout'
    )
    def create_checkout_session(self, request, pk=None):
        """
        Create a Stripe Checkout Session for an order.
        Returns a Stripe-hosted payment page URL.

        POST /api/orders/{id}/checkout/
        Response: { "checkout_url": "https://checkout.stripe.com/c/pay/..." }
        """
        import stripe
        from django.conf import settings as django_settings
        from django.utils import timezone

        order = self.get_object()

        # Validation
        if order.status != 'pending':
            return Response(
                {'error': f'Cannot create checkout for order with status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if timezone.now() > order.reserved_until:
            order.status = 'expired'
            order.save()
            return Response(
                {'error': 'Order reservation has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not django_settings.STRIPE_SECRET_KEY:
            return Response(
                {'error': 'Stripe is not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            success_url = django_settings.STRIPE_SUCCESS_URL.format(order_id=order.id)
            cancel_url = django_settings.STRIPE_CANCEL_URL.format(order_id=order.id)

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(order.price * 100),  # cents
                        'product_data': {
                            'name': f'Flight {order.flight.number} — Seat {order.seat_number}',
                            'description': (
                                f'Departure: {order.flight.departure_time.strftime("%Y-%m-%d %H:%M")} UTC'
                            ),
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                expires_at=int(max(
                    order.reserved_until,
                    timezone.now() + __import__('datetime').timedelta(minutes=31)
                ).timestamp()),  # Stripe requires >= 30 min from now
                metadata={
                    'order_id': order.id,
                    'user_id': order.user.id,
                    'flight_number': order.flight.number,
                    'seat_number': order.seat_number,
                },
            )

            # Store checkout session id on the order
            order.payment_intent_id = session.payment_intent or order.payment_intent_id
            order.save()

            return Response(
                {'checkout_url': session.url},
                status=status.HTTP_200_OK
            )

        except stripe.error.StripeError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



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