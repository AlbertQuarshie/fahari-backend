from rest_framework import generics, permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from fahari_backend.models import User, Room
from .serializers import RegisterSerializer, UserSerializer, RoomSerializer, BookingSerializer, HousekeepingAssignmentSerializer, MaintenanceRequestSerializer
from .permissions import IsAdmin, IsReceptionist, IsHousekeeper
from django_filters.rest_framework import DjangoFilterBackend
from fahari_backend.models import User, Room, Booking, HousekeepingAssignment, MaintenanceRequest


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logged out successfully."})
        except Exception:
            return Response({"detail": "Invalid token."}, status=400)


class MeView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['room_type', 'status', 'floor', 'capacity']
    search_fields = ['room_number', 'room_type']
    ordering_fields = ['price_per_night', 'floor']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'room', 'guest']
    ordering_fields = ['check_in_date', 'created_at']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'receptionist']:
            return Booking.objects.all()
        return Booking.objects.filter(guest=user)

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsReceptionist]
        elif self.action == 'destroy':
            permission_classes = [IsAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(guest=self.request.user)


class CancelBookingView(APIView):
    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk, guest=request.user)
            if booking.status in ['checked_in', 'checked_out']:
                return Response({"detail": "Cannot cancel this booking."}, status=400)
            booking.status = 'cancelled'
            booking.save()
            return Response({"detail": "Booking cancelled successfully."})
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=404)

class CheckInOutView(APIView):
    permission_classes = [IsReceptionist]

    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            action = request.data.get('action')

            if action == 'check_in':
                if booking.status != 'confirmed':
                    return Response({"detail": "Booking must be confirmed before check-in."}, status=400)
                booking.status = 'checked_in'
                booking.room.status = 'occupied'
                booking.room.save()

            elif action == 'check_out':
                if booking.status != 'checked_in':
                    return Response({"detail": "Guest must be checked in before check-out."}, status=400)
                booking.status = 'checked_out'
                booking.room.status = 'cleaning'
                booking.room.save()

            else:
                return Response({"detail": "Invalid action. Use 'check_in' or 'check_out'."}, status=400)

            booking.save()
            return Response({"detail": f"{action.replace('_', ' ').title()} successful.", "status": booking.status})

        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=404)


class ConfirmBookingView(APIView):
    permission_classes = [IsReceptionist]

    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            if booking.status != 'pending':
                return Response({"detail": "Only pending bookings can be confirmed."}, status=400)
            booking.status = 'confirmed'
            booking.save()
            return Response({"detail": "Booking confirmed.", "status": booking.status})
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=404)


class HousekeepingViewSet(viewsets.ModelViewSet):
    serializer_class = HousekeepingAssignmentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'receptionist']:
            return HousekeepingAssignment.objects.all()
        return HousekeepingAssignment.objects.filter(housekeeper=user)

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdmin]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsHousekeeper]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = MaintenanceRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'receptionist']:
            return MaintenanceRequest.objects.all()
        return MaintenanceRequest.objects.filter(reported_by=user)

    def get_permissions(self):
        if self.action == 'destroy':
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsHousekeeper]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)