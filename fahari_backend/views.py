from rest_framework import generics, permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from fahari_backend.models import User, Room
from .serializers import RegisterSerializer, UserSerializer, RoomSerializer, BookingSerializer, HousekeepingAssignmentSerializer, MaintenanceRequestSerializer, ReviewSerializer
from .permissions import IsAdmin, IsReceptionist, IsHousekeeper
from django_filters.rest_framework import DjangoFilterBackend
from fahari_backend.models import User, Room, Booking, HousekeepingAssignment, MaintenanceRequest, Review


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
class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Review.objects.all()
        return Review.objects.filter(is_approved=True)

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(guest=self.request.user)


class AdminDashboardView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        from django.utils import timezone
        from django.db.models import Sum, Count
        import datetime

        today = timezone.now().date()
        week_ago = today - datetime.timedelta(days=7)
        month_ago = today - datetime.timedelta(days=30)

        # revenue
        daily_revenue = Booking.objects.filter(
            status='checked_out',
            check_out_date=today
        ).aggregate(total=Sum('total_price'))['total'] or 0

        weekly_revenue = Booking.objects.filter(
            status='checked_out',
            check_out_date__gte=week_ago
        ).aggregate(total=Sum('total_price'))['total'] or 0

        monthly_revenue = Booking.objects.filter(
            status='checked_out',
            check_out_date__gte=month_ago
        ).aggregate(total=Sum('total_price'))['total'] or 0

        # booking stats
        total_bookings = Booking.objects.count()
        pending_bookings = Booking.objects.filter(status='pending').count()
        confirmed_bookings = Booking.objects.filter(status='confirmed').count()
        checked_in = Booking.objects.filter(status='checked_in').count()

        # room stats
        total_rooms = Room.objects.count()
        available_rooms = Room.objects.filter(status='available').count()
        occupied_rooms = Room.objects.filter(status='occupied').count()
        cleaning_rooms = Room.objects.filter(status='cleaning').count()

        # recent bookings
        recent_bookings = Booking.objects.select_related('guest', 'room').order_by('-created_at')[:5]
        recent_bookings_data = BookingSerializer(recent_bookings, many=True).data

        return Response({
            'revenue': {
                'daily': daily_revenue,
                'weekly': weekly_revenue,
                'monthly': monthly_revenue,
            },
            'bookings': {
                'total': total_bookings,
                'pending': pending_bookings,
                'confirmed': confirmed_bookings,
                'checked_in': checked_in,
            },
            'rooms': {
                'total': total_rooms,
                'available': available_rooms,
                'occupied': occupied_rooms,
                'cleaning': cleaning_rooms,
            },
            'recent_bookings': recent_bookings_data,
        })

class WalkInBookingView(APIView):
    permission_classes = [IsReceptionist]

    def post(self, request):
        serializer = BookingSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            guest_id = request.data.get('guest')
            try:
                guest = User.objects.get(pk=guest_id)
            except User.DoesNotExist:
                return Response({"detail": "Guest not found."}, status=404)
            booking = serializer.save(guest=guest, status='confirmed')
            return Response(BookingSerializer(booking).data, status=201)
        return Response(serializer.errors, status=400)


class DailyRosterView(APIView):
    permission_classes = [IsReceptionist]

    def get(self, request):
        from django.utils import timezone
        today = timezone.now().date()

        checking_in = Booking.objects.filter(
            check_in_date=today,
            status='confirmed'
        ).select_related('guest', 'room')

        checking_out = Booking.objects.filter(
            check_out_date=today,
            status='checked_in'
        ).select_related('guest', 'room')

        currently_in = Booking.objects.filter(
            status='checked_in'
        ).select_related('guest', 'room')

        return Response({
            'date': today,
            'checking_in': BookingSerializer(checking_in, many=True).data,
            'checking_out': BookingSerializer(checking_out, many=True).data,
            'currently_checked_in': BookingSerializer(currently_in, many=True).data,
        })


class GuestBookingHistoryView(APIView):
    permission_classes = [IsReceptionist]

    def get(self, request, guest_id):
        try:
            guest = User.objects.get(pk=guest_id)
            bookings = Booking.objects.filter(guest=guest).order_by('-created_at')
            return Response({
                'guest': UserSerializer(guest).data,
                'bookings': BookingSerializer(bookings, many=True).data
            })
        except User.DoesNotExist:
            return Response({"detail": "Guest not found."}, status=404)


class StaffListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        staff = User.objects.exclude(role='guest')
        serializer = UserSerializer(staff, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=201)
        return Response(serializer.errors, status=400)