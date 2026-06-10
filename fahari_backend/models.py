from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    ROLE_CHOICES = (
        ('guest', 'Guest'),
        ('receptionist', 'Receptionist'),
        ('housekeeper', 'Housekeeper'),
        ('admin', 'Admin'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='guest'
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    phone = models.CharField(max_length=20)

    profile_image = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='fahari_users',
        blank=True
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='fahari_users',
        blank=True
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class Room(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('cleaning', 'Cleaning'),
        ('maintenance', 'Maintenance'),
    )

    ROOM_TYPE_CHOICES = (
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
    )

    room_number = models.CharField(max_length=10, unique=True)

    room_type = models.CharField(
        max_length=20,
        choices=ROOM_TYPE_CHOICES
    )

    floor = models.IntegerField()

    capacity = models.IntegerField()

    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )

    image = models.ImageField(
        upload_to='rooms/',
        blank=True,
        null=True
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type})"

    class Meta:
        ordering = ['floor', 'room_number']

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
    )

    booking_reference = models.CharField(max_length=20, unique=True, blank=True)
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    early_check_in = models.BooleanField(default=False)
    late_check_out = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = 'FG-' + str(uuid.uuid4()).upper()[:8]
        if not self.total_price:
            delta = self.check_out_date - self.check_in_date
            self.total_price = delta.days * self.room.price_per_night
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_reference} - {self.guest.username} - Room {self.room.room_number}"

    class Meta:
        ordering = ['-created_at']