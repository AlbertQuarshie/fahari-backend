from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, LogoutView, MeView,
    RoomViewSet, BookingViewSet, CancelBookingView,
    CheckInOutView, ConfirmBookingView,
    HousekeepingViewSet, MaintenanceRequestViewSet,
    ReviewViewSet, AdminDashboardView,
    WalkInBookingView, DailyRosterView,
    GuestBookingHistoryView, StaffListView
)

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'housekeeping', HousekeepingViewSet, basename='housekeeping')
router.register(r'maintenance', MaintenanceRequestViewSet, basename='maintenance')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('bookings/<int:pk>/cancel/', CancelBookingView.as_view(), name='cancel-booking'),
    path('bookings/<int:pk>/checkinout/', CheckInOutView.as_view(), name='checkinout'),
    path('bookings/<int:pk>/confirm/', ConfirmBookingView.as_view(), name='confirm-booking'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('receptionist/walkin/', WalkInBookingView.as_view(), name='walkin-booking'),
    path('receptionist/roster/', DailyRosterView.as_view(), name='daily-roster'),
    path('receptionist/guest/<int:guest_id>/bookings/', GuestBookingHistoryView.as_view(), name='guest-history'),
    path('staff/', StaffListView.as_view(), name='staff-list'),
    path('', include(router.urls)),
]