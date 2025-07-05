"""
URL configuration for RenPark project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rent_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Home page
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('renter_dashboard/', views.renter_dashboard, name='renter_dashboard'),
    path('owner_dashboard/', views.owner_dashboard, name='owner_dashboard'),

    path('admin1/user-management/', views.user_management, name='user_management'),
    path('admin1/approve-user/<int:profile_id>/', views.approve_user, name='approve_user'),
    path('admin1/remove-user/<int:profile_id>/', views.remove_user, name='remove_user'),
    path('admin1/cars/', views.car_list, name='car_list'),
    path('admin1/car/<int:car_id>/', views.car_details, name='car_details'),
    path('admin1/car/<int:car_id>/bookings/', views.car_bookings, name='car_bookings'),
    path('admin1/booking/<int:booking_id>/', views.booking_details, name='booking_details'),
    path('admin1/car/<int:car_id>/reports/', views.car_reports, name='car_reports'),
    path('admin1/revenue/cars/', views.car_revenue, name='car_revenue'),
    path('admin1/payments/owners/', views.owner_payments, name='owner_payments'),

    path('renter/profile/', views.renter_profile, name='renter_profile'),
    path('renter/cars/browse', views.browse_cars, name='browse_cars'),
    path('renter/car/book/<int:car_id>/', views.book_car, name='book_car'),

    # Booking management
    path('renter/booking-history/', views.booking_history, name='booking_history'),
    path('renter/booking/pay/<int:booking_id>/', views.make_payment, name='make_payment'),
    path('renter/booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('renter/booking/close/<int:booking_id>/', views.close_booking, name='close_booking'),

    # Review and feedback
    path('renter/booking/review/<int:booking_id>/', views.submit_review, name='submit_review'),
    path('renter/reviews/', views.my_reviews, name='my_reviews'),

    path('owner/profile/', views.owner_profile, name='owner_profile'),
    path('owner/car/register', views.car_register, name='car_register'),
    path('owner/cars/', views.my_cars, name='my_cars'),
    path('owner/car/<int:car_id>/', views.car_details_owner, name='car_details_owner'),
    path('owner/earnings/', views.my_earnings, name='my_earnings'),
    path('owner/revenue/cars/', views.cars_revenue_owner, name='cars_revenue_owner'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)