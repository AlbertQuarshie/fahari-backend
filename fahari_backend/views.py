from rest_framework import generics, permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from fahari_backend.models import User, Room
from .serializers import RegisterSerializer, UserSerializer, RoomSerializer, BookingSerializer
from .permissions import IsAdmin, IsReceptionist
from django_filters.rest_framework import DjangoFilterBackend
from fahari_backend.models import User, Room, Booking


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