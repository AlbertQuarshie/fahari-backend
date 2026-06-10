from django.contrib import admin
from .models import User, Room


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