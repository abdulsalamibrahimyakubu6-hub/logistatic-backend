from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Shipment, ShipmentStatusLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone_number', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Profile', {'fields': ('role', 'phone_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Profile', {'fields': ('role', 'phone_number')}),
    )


class ShipmentStatusLogInline(admin.TabularInline):
    model = ShipmentStatusLog
    extra = 0
    readonly_fields = ('status', 'updated_by', 'notes', 'timestamp')
    can_delete = False


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'customer', 'driver', 'status', 'weight_kg', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('tracking_number', 'customer__username', 'customer__email', 'driver__username', 'delivery_address', 'pickup_address')
    readonly_fields = ('tracking_number', 'created_at', 'updated_at')
    inlines = [ShipmentStatusLogInline]


@admin.register(ShipmentStatusLog)
class ShipmentStatusLogAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'status', 'updated_by', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('shipment__tracking_number', 'notes', 'updated_by__username')
    readonly_fields = ('timestamp',)
