from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Shipment, ShipmentStatusLog

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Shipment)
admin.site.register(ShipmentStatusLog)
