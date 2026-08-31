from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# Create your models here.

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        DRIVER = 'DRIVER', 'Driver'
        CUSTOMER = 'CUSTOMER', 'Customer'
        
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone_number = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
class Shipment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Pickup'
        ASSIGNED = 'ASSIGNED', 'Driver Assigned'
        IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
        OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', 'Out for Delivery'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'
        
    tracking_number = models.CharField(max_length=30, unique=True, editable=False)
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='customer_shipments'
    )
    delivery_address = models.TextField()
    pickup_address = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': User.Role.DRIVER},
        related_name='driver_shipments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.tracking_number:
            while True:
                candidate = f"TRK-{uuid.uuid4().hex[:8].upper()}"
                if not Shipment.objects.filter(tracking_number=candidate).exists():
                    self.tracking_number = candidate
                    break
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.tracking_number} - {self.get_status_display()}"


class ShipmentStatusLog(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name="status_logs"
    )
    status = models.CharField(max_length=20, choices=Shipment.Status.choices)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.status}"