from rest_framework import serializers
from fahari_backend.models import User, Room, Booking, HousekeepingAssignment, MaintenanceRequest, Review, Payment
from datetime import date


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'password', 'confirm_password', 'phone', 'profile_image'
        )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(
            role='guest',
            is_active=True,
            **validated_data
        )


class StaffRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    STAFF_ROLES = ['receptionist', 'housekeeper', 'admin']

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'password', 'confirm_password', 'role', 'phone', 'profile_image'
        )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_role(self, value):
        if value not in self.STAFF_ROLES:
            raise serializers.ValidationError(f"Role must be one of: {', '.join(self.STAFF_ROLES)}")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(
            is_active=True,
            **validated_data
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'role',
            'phone',
            'profile_image'
        )


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = (
            'id',
            'room_number',
            'room_type',
            'floor',
            'capacity',
            'price_per_night',
            'status',
            'image',
            'description',
            'created_at'
        )

        read_only_fields = ('id', 'created_at')
from datetime import date

class BookingSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    guest_username = serializers.CharField(source='guest.username', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)

    class Meta:
        model = Booking
        fields = (
            'id',
            'booking_reference',
            'guest',
            'guest_username',
            'room',
            'room_number',
            'check_in_date',
            'check_out_date',
            'status',
            'total_price',
            'early_check_in',
            'late_check_out',
            'created_at',
        )
        read_only_fields = ('id', 'booking_reference', 'total_price', 'created_at', 'guest')

    def validate(self, data):
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        room = data.get('room')

        # check in must be before check out
        if check_in and check_out:
            if check_in >= check_out:
                raise serializers.ValidationError("Check-out date must be after check-in date.")
            if check_in < date.today():
                raise serializers.ValidationError("Check-in date cannot be in the past.")

        # check room availability
        if room and check_in and check_out:
            overlapping = Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed', 'checked_in'],
                check_in_date__lt=check_out,
                check_out_date__gt=check_in,
            )
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise serializers.ValidationError("Room is not available for the selected dates.")

        return data

class HousekeepingAssignmentSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    housekeeper_name = serializers.CharField(source='housekeeper.username', read_only=True)

    class Meta:
        model = HousekeepingAssignment
        fields = ('id', 'room', 'room_number', 'housekeeper', 'housekeeper_name', 'status', 'assigned_date', 'notes', 'updated_at')
        read_only_fields = ('id', 'assigned_date', 'updated_at')


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    reported_by_username = serializers.CharField(source='reported_by.username', read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = ('id', 'room', 'room_number', 'reported_by', 'reported_by_username', 'description', 'priority', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'reported_by', 'created_at', 'updated_at')

class ReviewSerializer(serializers.ModelSerializer):
    guest_username = serializers.CharField(source='guest.username', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'guest', 'guest_username', 'room', 'room_number', 'booking', 'rating', 'comment', 'is_approved', 'created_at')
        read_only_fields = ('id', 'guest', 'created_at')

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, data):
        booking = data.get('booking')
        if booking and booking.status != 'checked_out':
            raise serializers.ValidationError("You can only review after checkout.")
        if booking and booking.guest != self.context['request'].user:
            raise serializers.ValidationError("You can only review your own bookings.")
        return data

class PaymentSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source='booking.booking_reference', read_only=True)

    class Meta:
        model = Payment
        fields = ('id', 'booking', 'booking_reference', 'phone_number', 'amount', 'mpesa_checkout_id', 'mpesa_receipt', 'status', 'created_at')
        read_only_fields = ('id', 'mpesa_checkout_id', 'mpesa_receipt', 'status', 'created_at')