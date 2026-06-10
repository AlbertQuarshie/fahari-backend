from rest_framework import serializers
from fahari_backend.models import User, Room, Booking
from datetime import date


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=6
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
            'role',
            'phone',
            'profile_image'
        )

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'guest'),
            phone=validated_data.get('phone', ''),
            profile_image=validated_data.get('profile_image', None),
            is_active=True,
        )

        return user


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
        read_only_fields = ('id', 'booking_reference', 'total_price', 'created_at')

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