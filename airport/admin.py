from django.contrib import admin
from .models import Country, Airport, Airline, Airplane, Flight, Order, Ticket


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
    list_display = ('number', 'airplane', 'departure_time', 'status', 'price', 'tickets_sold', 'tickets_available')
    list_filter = ('status', 'departure_time')
    search_fields = ('number',)

    def tickets_sold(self, obj):
        return obj.tickets.filter(status='active').count()
    tickets_sold.short_description = 'Sold'

    def tickets_available(self, obj):
        occupied = obj.tickets.filter(status__in=['reserved', 'active']).count()
        return obj.airplane.capacity - occupied
    tickets_available.short_description = 'Available'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'flight', 'user', 'total_price', 'ticket_count',
        'status', 'payment_status', 'payment_intent_id',
        'reserved_until', 'created_at'
    )
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('user__username', 'flight__number', 'payment_intent_id')
    readonly_fields = ('total_price', 'payment_intent_id', 'payment_status', 'created_at', 'updated_at')

    def ticket_count(self, obj):
        return obj.tickets.count()
    ticket_count.short_description = 'Tickets'


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'flight', 'user', 'seat_number', 'price', 'status')
    list_filter = ('status',)
    search_fields = ('user__username', 'flight__number', 'seat_number')