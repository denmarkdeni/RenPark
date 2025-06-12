from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Profile, RenterDocument, CarDocument, Car, Booking, Payment, Payout, Invoice
from datetime import datetime
from decimal import Decimal
import os, uuid


def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == "POST":
        if 'signup' in request.POST:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            user_type = request.POST.get('user_type')

            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect('register')

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken.")
                return redirect('register')

            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user, role=user_type)
            messages.success(request, "Registration successful. Please sign in.")
            return redirect('register')  

        elif 'signin' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, "Logged in successfully.")
                return redirect('dashboard') 
            else:
                messages.error(request, "Invalid credentials.")
                return redirect('register')

    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('register')

def dashboard(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.profile.role == 'renter':
            return redirect('renter_dashboard')
        elif request.user.profile.role == 'owner':
            return redirect('owner_dashboard')
    else:
        return redirect('register')  

def admin_dashboard(request):
    return render (request, 'dashboards/admin_dashboard.html')

def renter_dashboard(request):
    return render (request, 'dashboards/renter_dashboard.html')

def owner_dashboard(request):
    return render (request, 'dashboards/owner_dashboard.html')

@login_required
def renter_profile(request):
    profile = request.user.profile
    if profile.role != 'renter':
        messages.error(request, "Access denied. You are not a renter.")
        return redirect('home')

    if request.method == 'POST':
        phone = request.POST.get('phone')
        location = request.POST.get('location')
        picture = request.FILES.get('picture')
        id_proof = request.FILES.get('id_proof')
        license = request.FILES.get('license')

        # Update profile
        profile.phone = phone
        profile.location = location
        if picture:
            if profile.picture and os.path.exists(profile.picture.path):
                os.remove(profile.picture.path)
            profile.picture = picture
        profile.save()

        # Save renter documents
        if id_proof:
            RenterDocument.objects.create(renter=profile, document_type='ID', document_file=id_proof)
        if license:
            RenterDocument.objects.create(renter=profile, document_type='License', document_file=license)

        messages.success(request, "Profile updated successfully!")
        return redirect('renter_profile')

    return render(request, 'profile/renter_profile.html', {'profile': profile})

@login_required
def owner_profile(request):
    profile = request.user.profile
    if profile.role != 'owner':
        messages.error(request, "Access denied. You are not a car owner.")
        return redirect('home')

    if request.method == 'POST':
        phone = request.POST.get('phone')
        location = request.POST.get('location')
        picture = request.FILES.get('picture')

        # Update profile
        profile.phone = phone
        profile.location = location
        if picture:
            if profile.picture and os.path.exists(profile.picture.path):
                os.remove(profile.picture.path)
            profile.picture = picture
        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('owner_profile')

    return render(request, 'profile/owner_profile.html', {'profile': profile})

@login_required
def car_register(request):
    profile = request.user.profile
    if profile.role != 'owner':
        messages.error(request, "Access denied. You are not a car owner.")
        return redirect('home')

    if request.method == 'POST':
        model = request.POST.get('model')
        plate_number = request.POST.get('plate_number')
        rent_rate = request.POST.get('rent_rate')
        description = request.POST.get('description')
        location = request.POST.get('location')
        rc_book = request.FILES.get('rc_book')
        insurance = request.FILES.get('insurance')
        picture = request.FILES.get('picture')

        # Create car instance
        try:
            car = Car.objects.create(
                owner=profile,
                model=model,
                plate_number=plate_number,
                rent_rate=rent_rate,
                description=description,
                location=location,
                is_available=True,
                picture=picture
            )

            # Save car documents
            if rc_book:
                CarDocument.objects.create(car=car, document_type='RC', document_file=rc_book)
            if insurance:
                CarDocument.objects.create(car=car, document_type='Insurance', document_file=insurance)

            messages.success(request, "Car registered successfully!")
            return redirect('car_register')
        except Exception as e:
            messages.error(request, f"Error registering car: {str(e)}")

    return render(request, 'cars/car_register.html')

@login_required
def browse_cars(request):
    profile = request.user.profile
    if profile.role != 'renter':
        messages.error(request, "Access denied. You are not a renter.")
        return redirect('home')

    # Fetch only available cars
    cars = Car.objects.filter(is_available=True)
    return render(request, 'cars/browse_cars.html', {'cars': cars})

@login_required
def book_car(request, car_id):
    profile = request.user.profile
    if profile.role != 'renter':
        messages.error(request, "Access denied. You are not a renter.")
        return redirect('home')

    car = get_object_or_404(Car, id=car_id, is_available=True)

    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            days = (end_date - start_date).days

            if days <= 0:
                messages.error(request, "End date must be after start date.")
                return redirect('book_car', car_id=car.id)

            total_amount = days * car.rent_rate
            Booking.objects.create(
                renter=profile,
                car=car,
                start_date=start_date,
                end_date=end_date,
                total_amount=total_amount,
                status='Pending'
            )
            car.is_available = False
            car.save()

            messages.success(request, "Car booked successfully!")
            return redirect('booking_history')
        except ValueError:
            messages.error(request, "Invalid date format.")
        except Exception as e:
            messages.error(request, f"Error booking car: {str(e)}")

    return render(request, 'cars/book_car.html', {'car': car})

@login_required
def booking_history(request):
    profile = request.user.profile
    if profile.role != 'renter':
        messages.error(request, "Access denied. You are not a renter.")
        return redirect('home')

    # Split bookings into current (Pending, Confirmed) and past (Completed, Cancelled)
    current_bookings = Booking.objects.filter(renter=profile, status__in=['Pending', 'Confirmed']).order_by('-created_at')
    past_bookings = Booking.objects.filter(renter=profile, status__in=['Completed', 'Cancelled']).order_by('-created_at')

    return render(request, 'cars/booking_history.html', {
        'current_bookings': current_bookings,
        'past_bookings': past_bookings
    })

@login_required
def make_payment(request, booking_id):
    profile = request.user.profile
    if profile.role != 'renter':
        messages.error(request, "Access denied. You are not a renter.")
        return redirect('home')

    booking = get_object_or_404(Booking, id=booking_id, renter=profile, status='Pending')

    if request.method == 'POST':
        # Create Payment record
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_amount,
            status='Completed',
            transaction_id=str(uuid.uuid4())  # Dummy transaction ID
        )

        # Update booking status
        booking.status = 'Confirmed'
        booking.save()

        messages.success(request, "Payment successful! Booking confirmed.")
        return redirect('booking_history')

    return render(request, 'payment/make_payment.html', {'booking': booking})

@login_required
def cancel_booking(request, booking_id):
    profile = request.user.profile
    if profile.role != 'renter':
        messages.error(request, "Access denied. You are not a renter.")
        return redirect('home')

    booking = get_object_or_404(Booking, id=booking_id, renter=profile, status__in=['Pending', 'Confirmed'])
    car = booking.car

    booking.status = 'Cancelled'
    booking.save()
    car.is_available = True
    car.save()

    messages.success(request, "Booking cancelled successfully!")
    return redirect('booking_history')

@login_required
def close_booking(request, booking_id):
    profile = request.user.profile
    if profile.role != 'renter':
        messages.error(request, "Access denied. You are not a renter.")
        return redirect('home')

    booking = get_object_or_404(Booking, id=booking_id, renter=profile, status='Confirmed')
    car = booking.car

    booking.status = 'Completed'
    booking.save()
    car.is_available = True
    car.save()

     # Create Payout for the owner
    Payout.objects.create(
        owner=booking.car.owner,
        booking=booking,
        amount=booking.total_amount * Decimal('0.9'),  # Assuming 10% platform fee
        status='Pending'
    )

    # Create Invoice for the renter
    Invoice.objects.create(
        booking=booking,
        invoice_number=f"INVOICE-{booking.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        amount=booking.total_amount
    )

    messages.success(request, "Booking closed successfully!")
    return redirect('booking_history')