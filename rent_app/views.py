from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Profile

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
                return redirect('dashboard') 
            else:
                messages.error(request, "Invalid credentials.")
                return redirect('register')

    return render(request, 'register.html')

def logout_view(request):
    logout(request)
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
def submit_profile(request):
    if request.method == "POST":
        phone = request.POST['phone']
        vehicle_number = request.POST.get('vehicle_number')
        vehicle_type = request.POST.get('vehicle_type')
        license_number = request.POST.get('license_number')
        location = request.POST.get('location')
        id_proof = request.FILES.get('id_proof')

        profile, created = Profile.objects.update_or_create(
            user=request.user,
            defaults={
                'phone': phone,
                'location': location,
                'vehicle_number': vehicle_number,
                'vehicle_type': vehicle_type,
                'license_number': license_number,
                'id_proof': id_proof,
                'status': 'Pending',
            }
        )
        messages.success(request, "Profile submitted.")
        return redirect('dashboard')

    return render(request, 'profile.html')