from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.utils import timezone
from .models import Profile, RenterDocument, CarDocument, Car, Booking, Payment
from .models import Payout, Invoice, OwnerEarnings, ReportedIssue, Review
from datetime import datetime
from decimal import Decimal
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from django.core.files.base import ContentFile
import os, uuid, io


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

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. You are not an admin.")
        return redirect('home')

    # Get top 4 rented cars with owner and booking count
    top_rented_cars = (
        Car.objects.annotate(booking_count=Count('bookings'))
        .filter(bookings__status__in=['Confirmed', 'Completed'])
        .order_by('-booking_count')[:4]
    )

    top_cars_data = [
        {
            'car_model': car.model,
            'owner_name': car.owner.user.username,
            'booking_count': car.booking_count,
            'performance': f"+{car.booking_count * 10}%"
        }
        for car in top_rented_cars
    ]

    # Get filter month from request (default to current month)
    selected_month = request.GET.get('month', f"{timezone.now().strftime('%B %Y')}")
    try:
        filter_date = datetime.strptime(selected_month, '%B %Y')
        month = filter_date.month
        year = filter_date.year
    except ValueError:
        month = timezone.now().month
        year = timezone.now().year

    # Get recent rented cars (bookings) for the selected month
    recent_bookings = (
        Booking.objects.filter(
            status__in=['Confirmed', 'Completed'],
            created_at__year=year,
            created_at__month=month
        )
        .select_related('car', 'car__owner')
        .order_by('-created_at')[:5]
    )

    # Calculate demand for each car based on total bookings
    car_booking_counts = (
        Booking.objects.filter(status__in=['Confirmed', 'Completed'])
        .values('car')
        .annotate(booking_count=Count('id'))
    )
    booking_counts = {item['car']: item['booking_count'] for item in car_booking_counts}
    max_bookings = max(booking_counts.values(), default=0) if booking_counts else 0

    recent_cars_data = []
    for booking in recent_bookings:
        car = booking.car
        booking_count = booking_counts.get(car.id, 0)
        # Determine demand based on booking count
        if max_bookings > 0:
            demand_ratio = booking_count / max_bookings
            if demand_ratio >= 0.75:
                demand = 'High'
                demand_class = 'warning'
            elif demand_ratio >= 0.4:
                demand = 'Medium'
                demand_class = 'primary'
            else:
                demand = 'Low'
                demand_class = 'info'
        else:
            demand = 'Low'
            demand_class = 'info'

        recent_cars_data.append({
            'owner_name': car.owner.user.username,
            'owner_location': car.owner.location or 'N/A',
            'owner_picture': car.owner.picture.url if car.owner.picture else '/static/dashboard/images/profile/user-1.jpg',
            'car_name': car.model,
            'demand': demand,
            'demand_class': demand_class,
            'price': f"₹{booking.total_amount}"
        })

    # Prepare month options for dropdown (last 3 months including current)
    current_date = timezone.now()
    month_options = []
    for i in range(3):
        month_date = current_date - timezone.timedelta(days=i * 30)
        month_options.append(month_date.strftime('%B %Y'))

    # Fetch recent reviews for feedback section
    recent_reviews = Review.objects.select_related('renter', 'booking__car').order_by('-created_at')[:4]
    feedback_data = [
        {
            'renter_name': review.renter.user.username,
            'renter_picture': review.renter.picture.url if review.renter.picture else '/static/dashboard/images/profile/default.jpg',
            'comment': review.comment or "No comment provided.",
            'rating': review.rating,
            'status': 'Approved',  # For now, assume all reviews are approved
            'status_class': 'success',
            'created_at': review.created_at.strftime('%B %d, %Y')
        }
        for review in recent_reviews
    ]

    # Issue Reports
    recent_issues = ReportedIssue.objects.select_related('reported_by').order_by('-created_at')[:4]
    issues_data = [
        {
            'reported_by_name': issue.reported_by.user.username,
            'reported_by_picture': issue.reported_by.picture.url if issue.reported_by.picture else '/static/dashboard/images/profile/default.jpg',
            'description': issue.description,
            'status': issue.status,
            'status_class': 'info' if issue.status == 'Open' else 'warning' if issue.status == 'In Progress' else 'success',
            'created_at': issue.created_at.strftime('%B %d, %Y')
        }
        for issue in recent_issues
    ]

    return render(request, 'dashboards/admin_dashboard.html', {
        'top_cars': top_cars_data,
        'recent_cars': recent_cars_data,
        'month_options': month_options,
        'selected_month': selected_month,
        'feedback': feedback_data,
        'issues': issues_data
    })

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
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_amount,
            status='Completed',
            transaction_id=str(uuid.uuid4())
        )

        booking.status = 'Confirmed'
        booking.save()

        platform_fee = booking.total_amount * Decimal('0.1')
        payout_amount = booking.total_amount * Decimal('0.9')
        Payout.objects.create(
            owner=booking.car.owner,
            booking=booking,
            amount=payout_amount,
            platform_fee=platform_fee,
            status='Pending'
        )

        owner_earnings, created = OwnerEarnings.objects.get_or_create(
            owner=booking.car.owner,
            defaults={'total_earnings': Decimal('0.00'), 'pending_earnings': Decimal('0.00'), 'platform_fees': Decimal('0.00')}
        )
        owner_earnings.pending_earnings += payout_amount
        owner_earnings.platform_fees += platform_fee
        owner_earnings.save()

        # Generate PDF invoice
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setFont("Helvetica", 12)

        # Header
        p.drawString(1 * inch, 10 * inch, "RenPark Invoice")
        p.drawString(1 * inch, 9.5 * inch, f"Invoice Number: INVOICE-{booking.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        p.drawString(1 * inch, 9.2 * inch, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Renter Info
        p.drawString(1 * inch, 8.5 * inch, "Renter Information:")
        p.drawString(1 * inch, 8.2 * inch, f"Name: {booking.renter.user.username}")
        p.drawString(1 * inch, 7.9 * inch, f"Phone: {booking.renter.phone or 'N/A'}")

        # Owner Info
        p.drawString(1 * inch, 7.2 * inch, "Owner Information:")
        p.drawString(1 * inch, 6.9 * inch, f"Name: {booking.car.owner.user.username}")
        p.drawString(1 * inch, 6.6 * inch, f"Phone: {booking.car.owner.phone or 'N/A'}")

        # Booking Info
        p.drawString(1 * inch, 6 * inch, "Booking Details:")
        p.drawString(1 * inch, 5.7 * inch, f"Car: {booking.car.model} ({booking.car.plate_number})")
        p.drawString(1 * inch, 5.4 * inch, f"Start Date: {booking.start_date}")
        p.drawString(1 * inch, 5.1 * inch, f"End Date: {booking.end_date}")
        p.drawString(1 * inch, 4.8 * inch, f"Total Amount: ₹{booking.total_amount}")

        # Financial Breakdown
        p.drawString(1 * inch, 4.2 * inch, "Financial Breakdown:")
        p.drawString(1 * inch, 3.9 * inch, f"Amount Paid by Renter: ₹{booking.total_amount}")
        p.drawString(1 * inch, 3.6 * inch, f"Platform Fee (10%): ₹{platform_fee}")
        p.drawString(1 * inch, 3.3 * inch, f"Owner Payout: ₹{payout_amount}")

        p.showPage()
        p.save()

        # Save PDF to Invoice
        pdf_name = f"invoice_{booking.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_file = ContentFile(buffer.getvalue(), pdf_name)

        invoice = Invoice.objects.create(
            booking=booking,
            invoice_number=f"INVOICE-{booking.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            amount=booking.total_amount,
            pdf_file=pdf_file
        )

        buffer.close()

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

    try:
        payout = Payout.objects.get(booking=booking, status='Pending')
        payout.status = 'Completed'
        payout.payout_date = datetime.now()
        payout.save()

        owner_earnings = OwnerEarnings.objects.get(owner=booking.car.owner)
        owner_earnings.pending_earnings -= payout.amount
        owner_earnings.total_earnings += payout.amount
        owner_earnings.save()
    except (Payout.DoesNotExist, OwnerEarnings.DoesNotExist):
        messages.error(request, "Payout or earnings record not found.")
        return redirect('booking_history')

    messages.success(request, "Booking closed successfully!")
    return redirect('booking_history')

@login_required
def submit_review(request, booking_id):
    profile = request.user.profile
    if profile.role != 'renter':
        messages.error(request, "Access denied. You are not a renter.")
        return redirect('home')

    booking = get_object_or_404(Booking, id=booking_id, renter=profile, status='Completed')
    if hasattr(booking, 'review'):
        messages.error(request, "You have already reviewed this booking.")
        return redirect('booking_history')

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        issue = request.POST.get('issue')

        Review.objects.create(
            booking=booking,
            renter=profile,
            rating=rating,
            comment=comment if comment else None
        )

        if issue:
            ReportedIssue.objects.create(
                reported_by=profile,
                car=booking.car,
                booking=booking,
                description=issue
            )

        messages.success(request, "Review submitted successfully!")
        return redirect('booking_history')

    return render(request, 'cars/submit_review.html', {'booking': booking})

@login_required
def my_reviews(request):
    profile = request.user.profile
    if profile.role != 'renter':
        messages.error(request, "Access denied. You are not a renter.")
        return redirect('home')

    reviews = Review.objects.filter(renter=profile).order_by('-created_at')
    return render(request, 'cars/my_reviews.html', {'reviews': reviews})

@login_required
def user_management(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. You are not an admin.")
        return redirect('register')
 
    users = Profile.objects.all().select_related('user')
    users_data = [
        {
            'id': profile.id,
            'username': profile.user.username,
            'role': profile.role,
            'phone': profile.phone,
            'location': profile.location,
            'picture_url': profile.picture.url if profile.picture else '/static/dashboard/images/profile/user-1.jpg',
            'is_approved': profile.is_approved
        }
        for profile in users
    ]

    return render(request, 'admin/user_management.html', {'users': users_data})

@login_required
def approve_user(request, profile_id):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. You are not an admin.")
        return redirect('home')

    profile = get_object_or_404(Profile, id=profile_id)
    if profile.role != 'admin':
        profile.is_approved = True
        profile.save()
        messages.success(request, f"User {profile.user.username} has been approved.")
    return redirect('user_management')

@login_required
def remove_user(request, profile_id):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. You are not an admin.")
        return redirect('home')

    profile = get_object_or_404(Profile, id=profile_id)
    if profile.role != 'admin':
        user = profile.user
        profile.delete()
        user.delete()
        messages.success(request, f"User {user.username} has been removed.")
    return redirect('user_management')

@login_required
def car_list(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. You are not an admin.")
        return redirect('home')

    cars = Car.objects.all().select_related('owner')
    cars_data = [
        {
            'model': car.model,
            'plate_number': car.plate_number,
            'owner_name': car.owner.user.username,
            'is_available': car.is_available,
            'location': car.location,
            'picture': car.picture.url if car.picture else None
        }
        for car in cars
    ]

    return render(request, 'admin/car_list.html', {'cars': cars_data})