from django.contrib import admin
from .models import User, Room, Booking


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'role',
        'phone',
        'is_active'
    )

    list_filter = (
        'role',
        'is_active'
    )

    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email'
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'room_number',
        'room_type',
        'floor',
        'capacity',
        'price_per_night',
        'status'
    )

    list_filter = (
        'room_type',
        'status',
        'floor'
    )

    search_fields = (
        'room_number',
    )

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'guest', 'room', 'check_in_date', 'check_out_date', 'status', 'total_price')
    list_filter = ('status',)
    search_fields = ('booking_reference', 'guest__username', 'room__room_number')