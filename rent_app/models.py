from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import date
from decimal import Decimal

# Existing Profile model (included for reference, not modified)
class Profile(models.Model):
    ROLE_CHOICES = (
        ('renter', 'Renter'),
        ('owner', 'Car Owner'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Car model for car owner to list vehicles
class Car(models.Model):
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, limit_choices_to={'role': 'owner'})
    model = models.CharField(max_length=100)
    plate_number = models.CharField(max_length=20, unique=True)
    rent_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100)
    picture = models.ImageField(upload_to='car_pictures/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.model} - {self.plate_number}"

# CarDocument model for RC Book, insurance, etc.
class CarDocument(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=(('RC', 'RC Book'), ('Insurance', 'Insurance'), ('Other', 'Other')))
    document_file = models.FileField(upload_to='car_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=(('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')), default='Pending')

    def __str__(self):
        return f"{self.car.model} - {self.document_type}"

# Renter's ID proof for verification
class RenterDocument(models.Model):
    renter = models.ForeignKey(Profile, on_delete=models.CASCADE, limit_choices_to={'role': 'renter'})
    document_type = models.CharField(max_length=50, choices=(('ID', 'ID Proof'), ('License', 'Driving License')))
    document_file = models.FileField(upload_to='renter_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=(('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')), default='Pending')

    def __str__(self):
        return f"{self.renter.user.username} - {self.document_type}"

# Booking model for renter to book cars
class Booking(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    )

    renter = models.ForeignKey(Profile, on_delete=models.CASCADE, limit_choices_to={'role': 'renter'}, related_name='bookings')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.renter.user.username} - {self.car.model} ({self.start_date} to {self.end_date})"

    # Ensure booking dates are valid
    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")
        if self.start_date < date.today():
            raise ValidationError("Start date cannot be in the past.")

# Payment model for tracking renter payments (dummy)
class Payment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.booking} - {self.amount}"

# Invoice model for generating invoices/receipts
class Invoice(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    issued_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} for {self.booking}"

# Payout model for car owner earnings
class Payout(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, limit_choices_to={'role': 'owner'}, related_name='payouts')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payout_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payout {self.amount} to {self.owner.user.username}"
    
class OwnerEarnings(models.Model):
    owner = models.OneToOneField(Profile, on_delete=models.CASCADE, limit_choices_to={'role': 'owner'})
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    pending_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    platform_fees = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Earnings for {self.owner.user.username} - Total: {self.total_earnings}"

# ReportedIssue model for admin to handle issues
class ReportedIssue(models.Model):
    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    )

    reported_by = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reported_issues')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='issues', blank=True, null=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='issues', blank=True, null=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Issue by {self.reported_by.user.username} - {self.status}"
    
class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    renter = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews', limit_choices_to={'role': 'renter'})
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # 1 to 5 stars
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.renter.user.username} for Booking {self.booking.id}"