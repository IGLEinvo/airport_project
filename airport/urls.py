from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CountryListCreateView, CountryDetailView,
    AirportViewSet, AirlineViewSet, 
    AirplaneViewSet, FlightViewSet, TicketViewSet
)

router = DefaultRouter()
router.register('airports', AirportViewSet)
router.register('airlines', AirlineViewSet)
router.register('airplanes', AirplaneViewSet)
router.register('flights', FlightViewSet)
router.register('tickets', TicketViewSet)

urlpatterns = [
    # GenericAPIView-based Country endpoints
    path('countries/', CountryListCreateView.as_view(), name='country-list'),
    path('countries/<int:pk>/', CountryDetailView.as_view(), name='country-detail'),
    
    # ViewSet-based endpoints
    path('', include(router.urls)),
]