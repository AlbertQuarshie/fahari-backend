from rest_framework import generics, permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Room, RoomImage
from .serializers import RegisterSerializer, StaffRegisterSerializer, UserSerializer, RoomSerializer, RoomImageSerializer, BookingSerializer, HousekeepingAssignmentSerializer, MaintenanceRequestSerializer, ReviewSerializer, PaymentSerializer, ContactMessageSerializer
from .permissions import IsAdmin, IsReceptionist, IsHousekeeper
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Room, Booking, HousekeepingAssignment, MaintenanceRequest, Review, Payment, ContactMessage
from .mpesa import stk_push, stk_query, mpesa_success_code
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from datetime import date
import logging
import requests

logger = logging.getLogger(__name__)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class StaffRegisterView(generics.CreateAPIView):
    serializer_class = StaffRegisterSerializer
    permission_classes = [IsAdmin]


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logged out successfully."})
        except Exception:
            return Response({"detail": "Invalid token."}, status=400)

class UserDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

    def patch(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

    def delete(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
            if user.is_superuser:
                return Response({"detail": "Cannot delete superuser."}, status=400)
            user.delete()
            return Response({"detail": "User deleted successfully."}, status=204)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)


class UserListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        role = request.query_params.get('role', None)
        users = User.objects.all()
        if role:
            users = users.filter(role=role)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class UpdateProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({"detail": "Both old and new password required."}, status=400)

        if not request.user.check_password(old_password):
            return Response({"detail": "Old password is incorrect."}, status=400)

        if len(new_password) < 6:
            return Response({"detail": "New password must be at least 6 characters."}, status=400)

        request.user.set_password(new_password)
        request.user.save()
        return Response({"detail": "Password changed successfully."})



class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['room_type', 'status', 'floor', 'capacity']
    search_fields = ['room_number', 'room_type']
    ordering_fields = ['price_per_night', 'floor']

    def get_queryset(self):
        queryset = Room.objects.all()
        check_in = self.request.query_params.get('check_in')
        check_out = self.request.query_params.get('check_out')

        if check_in and check_out:
            try:
                ci = date.fromisoformat(check_in)
                co = date.fromisoformat(check_out)
            except ValueError:
                ci = co = None

            if ci and co and ci < co:
                conflicting_room_ids = Booking.objects.filter(
                    status__in=['pending', 'confirmed', 'checked_in'],
                    check_in_date__lt=co,
                    check_out_date__gt=ci,
                ).values_list('room_id', flat=True)
                queryset = queryset.exclude(id__in=conflicting_room_ids).exclude(status='maintenance')

        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]


class RoomImageViewSet(viewsets.ModelViewSet):
    serializer_class = RoomImageSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['room']

    def get_queryset(self):
        return RoomImage.objects.all()

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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            if request.user.role in ['admin', 'receptionist']:
                booking = Booking.objects.get(pk=pk)
            else:
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
        if user.role in ['admin', 'receptionist', 'housekeeper']:
            return MaintenanceRequest.objects.all()
        return MaintenanceRequest.objects.filter(reported_by=user)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsHousekeeper]
        else:  # destroy
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)  
class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        # Show all reviews - no approval needed
        return Review.objects.all().order_by('-created_at')

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdmin]
        elif self.action == 'my_reviews':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(guest=self.request.user)

    def my_reviews(self, request):
        """Get reviews submitted by current user"""
        from rest_framework.decorators import action
        reviews = Review.objects.filter(guest=request.user).order_by('-created_at')
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)


class ContactMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ContactMessageSerializer
    queryset = ContactMessage.objects.all()

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        contact_message = serializer.save()
        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": "Fahari Grand Hotel <onboarding@resend.dev>",
                    "to": [settings.CONTACT_NOTIFICATION_EMAIL],
                    "subject": f"Fahari Grand — New Contact Message: {contact_message.subject}",
                    "text": (
                        f"You have a new message from the Fahari Grand website.\n\n"
                        f"Name: {contact_message.name}\n"
                        f"Email: {contact_message.email}\n"
                        f"Phone: {contact_message.phone or 'Not provided'}\n\n"
                        f"Message:\n{contact_message.message}\n\n"
                        f"— Sent {contact_message.created_at.strftime('%d %b %Y, %H:%M')}"
                    ),
                },
                timeout=10,
            )
            if response.status_code >= 400:
                logger.error("Resend API error %s: %s", response.status_code, response.text)
        except Exception:
            logger.exception("Failed to send contact notification email")


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

        # staff stats
        total_staff = User.objects.exclude(role='guest').count()
        receptionist_count = User.objects.filter(role='receptionist').count()
        housekeeper_count = User.objects.filter(role='housekeeper').count()
        admin_count = User.objects.filter(role='admin').count()
        total_guests = User.objects.filter(role='guest').count()

        # payment stats
        pending_payments = Payment.objects.filter(status='pending').count()
        completed_payments = Payment.objects.filter(status='completed').count()
        failed_payments = Payment.objects.filter(status='failed').count()

        # review stats
        pending_reviews = Review.objects.filter(is_approved=False).count()
        approved_reviews = Review.objects.filter(is_approved=True).count()

        # housekeeping stats
        dirty_rooms = HousekeepingAssignment.objects.filter(status='dirty').count()
        cleaning_in_progress = HousekeepingAssignment.objects.filter(status='cleaning').count()
        clean_rooms = HousekeepingAssignment.objects.filter(status='clean').count()
        inspected_rooms = HousekeepingAssignment.objects.filter(status='inspected').count()

        # maintenance stats
        open_maintenance = MaintenanceRequest.objects.filter(status='open').count()
        in_progress_maintenance = MaintenanceRequest.objects.filter(status='in_progress').count()
        resolved_maintenance = MaintenanceRequest.objects.filter(status='resolved').count()

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
            'staff': {
                'total': total_staff,
                'receptionists': receptionist_count,
                'housekeepers': housekeeper_count,
                'admins': admin_count,
                'guests': total_guests,
            },
            'payments': {
                'pending': pending_payments,
                'completed': completed_payments,
                'failed': failed_payments,
            },
            'reviews': {
                'pending_approval': pending_reviews,
                'approved': approved_reviews,
            },
            'housekeeping': {
                'dirty': dirty_rooms,
                'cleaning': cleaning_in_progress,
                'clean': clean_rooms,
                'inspected': inspected_rooms,
            },
            'maintenance': {
                'open': open_maintenance,
                'in_progress': in_progress_maintenance,
                'resolved': resolved_maintenance,
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
        serializer = StaffRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=201)
        return Response(serializer.errors, status=400)


def _apply_stk_result(payment, result_code, callback_metadata=None):
    if mpesa_success_code(result_code):
        receipt = ""
        if callback_metadata:
            items = callback_metadata.get("Item", [])
            receipt = next(
                (item["Value"] for item in items if item.get("Name") == "MpesaReceiptNumber"),
                "",
            )
        payment.mpesa_receipt = receipt
        payment.status = "completed"
        payment.booking.status = "confirmed"
        payment.booking.save(update_fields=["status", "updated_at"])
    else:
        payment.status = "failed"

    payment.save(update_fields=["mpesa_receipt", "status", "updated_at"])


def _sync_pending_payment(payment):
    if payment.status != "pending" or not payment.mpesa_checkout_id:
        return payment

    response = stk_query(payment.mpesa_checkout_id)
    if response.get("error"):
        return payment

    result_code = response.get("ResultCode")
    if result_code is None:
        return payment

    if mpesa_success_code(result_code):
        _apply_stk_result(payment, result_code)
    elif int(result_code) != 0:
        payment.status = "failed"
        payment.save(update_fields=["status", "updated_at"])

    return payment


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsReceptionist]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_queryset(self):
        return Payment.objects.select_related('booking').order_by('-created_at')


class InitiatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(pk=booking_id, guest=request.user)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=404)

        if booking.status not in ['pending', 'confirmed']:
            return Response({"detail": "Booking cannot be paid at this stage."}, status=400)

        if hasattr(booking, 'payment') and booking.payment.status == 'completed':
            return Response({"detail": "Booking already paid."}, status=400)

        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({"detail": "Phone number is required."}, status=400)

        response = stk_push(
            phone_number=phone_number,
            amount=booking.total_price,
            booking_reference=booking.booking_reference,
        )

        if response.get("error"):
            return Response({"detail": response["detail"]}, status=502)

        if str(response.get("ResponseCode")) != "0":
            return Response(
                {
                    "detail": response.get("ResponseDescription", "Failed to initiate payment."),
                    "mpesa_response": response,
                },
                status=400,
            )

        payment, created = Payment.objects.get_or_create(
            booking=booking,
            defaults={
                "phone_number": phone_number,
                "amount": booking.total_price,
                "mpesa_checkout_id": response.get("CheckoutRequestID", ""),
                "status": "pending",
            },
        )
        if not created:
            payment.phone_number = phone_number
            payment.amount = booking.total_price
            payment.mpesa_checkout_id = response.get("CheckoutRequestID", "")
            payment.status = "pending"
            payment.mpesa_receipt = ""
            payment.save()

        return Response(
            {
                "detail": "STK push sent successfully. Check your phone.",
                "payment": PaymentSerializer(payment).data,
                "checkout_request_id": response.get("CheckoutRequestID"),
                "booking_reference": booking.booking_reference,
                "amount": booking.total_price,
            }
        )


class PaymentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, booking_id):
        try:
            booking = Booking.objects.get(pk=booking_id, guest=request.user)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=404)

        if not hasattr(booking, "payment"):
            return Response({"detail": "No payment found for this booking."}, status=404)

        payment = _sync_pending_payment(booking.payment)
        return Response(PaymentSerializer(payment).data)


@method_decorator(csrf_exempt, name="dispatch")
class MpesaCallbackView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        data = request.data
        logger.info("M-Pesa callback received: %s", data)

        try:
            stk_callback = data["Body"]["stkCallback"]
            result_code = stk_callback["ResultCode"]
            checkout_id = stk_callback["CheckoutRequestID"]
            callback_metadata = stk_callback.get("CallbackMetadata")

            payment = Payment.objects.get(mpesa_checkout_id=checkout_id)
            _apply_stk_result(payment, result_code, callback_metadata)
            return Response({"ResultCode": 0, "ResultDesc": "Success"})

        except Payment.DoesNotExist:
            logger.error("M-Pesa callback for unknown checkout ID: %s", data)
            return Response({"ResultCode": 0, "ResultDesc": "Success"})

        except (KeyError, TypeError) as exc:
            logger.error("Invalid M-Pesa callback payload: %s", exc)
            return Response({"ResultCode": 1, "ResultDesc": "Invalid payload"}, status=400)

        except Exception:
            logger.exception("M-Pesa callback processing failed")
            return Response({"ResultCode": 1, "ResultDesc": "Processing failed"}, status=500)