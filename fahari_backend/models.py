from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField
import uuid

# User Models
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

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    
    profile_image = CloudinaryField(
        'image',
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

# Room models
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

    image = CloudinaryField(
        'image',
        blank=True,
        null=True
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type})"

    class Meta:
        ordering = ['floor', 'room_number']


# Room Gallery Images (multiple photos per room - bedroom, bathroom, living area, etc.)
class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images')

    image = CloudinaryField('image')

    caption = models.CharField(max_length=100, blank=True)

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Room {self.room.room_number} ({self.caption or self.pk})"

    class Meta:
        ordering = ['order', 'created_at']


# Booking Models
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


# Housekeeping Models
class HousekeepingAssignment(models.Model):
    STATUS_CHOICES = (
        ('dirty', 'Dirty'),
        ('cleaning', 'Cleaning'),
        ('clean', 'Clean'),
        ('inspected', 'Inspected'),
    )

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='housekeeping_assignments')
    housekeeper = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='dirty')
    assigned_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.room.room_number} - {self.housekeeper.username} - {self.status}"

    class Meta:
        ordering = ['-assigned_date']

# Maintenance Requests
class MaintenanceRequest(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    )

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='maintenance_requests')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_requests')
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.room.room_number} - {self.priority} - {self.status}"

    class Meta:
        ordering = ['-created_at']


# Review Models
class Review(models.Model):
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.guest.username} for Room {self.room.room_number} - {self.rating}★"

    class Meta:
        ordering = ['-created_at']


# Mpesa Payment Model
class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_checkout_id = models.CharField(max_length=100, blank=True)
    mpesa_receipt = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for {self.booking.booking_reference} - {self.status}"

# Contact Messages
class ContactMessage(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('read', 'Read'),
        ('responded', 'Responded'),
    )

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

    class Meta:
        ordering = ['-created_at']