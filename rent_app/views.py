from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
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
                return redirect('home') 
            else:
                messages.error(request, "Invalid credentials.")
                return redirect('register')

    return render(request, 'register.html')
