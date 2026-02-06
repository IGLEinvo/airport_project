from django.contrib import admin
from .models import Country, Airport, Airline, Airplane, Flight, Ticket

# Using @admin.register decorator for each model
# This allows customizing column display in the list view

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'country')
    list_filter = ('country',)
    search_fields = ('name', 'code')

@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ('name', 'airport')

@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'airline')
    list_filter = ('airline',)

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('number', 'airplane', 'departure_time', 'status')
    list_filter = ('status', 'departure_time')
    search_fields = ('number',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'flight', 'user', 'seat_number', 'status')
    list_filter = ('status',)