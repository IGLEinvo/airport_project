from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CountryViewSet, AirportViewSet, AirlineViewSet, 
    AirplaneViewSet, FlightViewSet, TicketViewSet
)

router = DefaultRouter()
router.register('countries', CountryViewSet)
router.register('airports', AirportViewSet)
router.register('airlines', AirlineViewSet)
router.register('airplanes', AirplaneViewSet)
router.register('flights', FlightViewSet)
router.register('tickets', TicketViewSet)

urlpatterns = [
    path('', include(router.urls)),
]