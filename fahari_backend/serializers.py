from rest_framework import serializers
from fahari_backend.models import User, Room


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