from rest_framework import serializers
from .models import User, Shipment, ShipmentStatusLog


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'phone_number', 'first_name', 'last_name']
        read_only_fields = ['id']
        
    def create(self, validated_data):
        request = self.context.get('request')
        is_admin = bool(
            request
            and request.user
            and request.user.is_authenticated
            and (request.user.role == User.Role.ADMIN or request.user.is_staff or request.user.is_superuser)
        )
        if not is_admin and validated_data.get('role') == User.Role.ADMIN:
            validated_data['role'] = User.Role.CUSTOMER
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        is_admin = bool(
            request
            and request.user
            and request.user.is_authenticated
            and (request.user.role == User.Role.ADMIN or request.user.is_staff or request.user.is_superuser)
        )
        if not is_admin and 'role' in validated_data:
            validated_data.pop('role')
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ShipmentStatusLogSerializer(serializers.ModelSerializer):
    updated_by = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ShipmentStatusLog
        fields = ['id', 'status', 'status_display', 'updated_by', 'notes', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class ShipmentSerializer(serializers.ModelSerializer):
    customer = serializers.StringRelatedField(read_only=True)
    driver = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_logs = ShipmentStatusLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = Shipment
        fields = [
            'id',
            'tracking_number',
            'customer',
            'driver',
            'delivery_address',
            'pickup_address',
            'status',
            'status_display',
            'weight_kg',
            'status_logs',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'tracking_number',
            'customer',
            'driver',
            'status',
            'created_at',
            'updated_at',
        ]


class AssignDriverSerializer(serializers.Serializer):
    driver_id = serializers.IntegerField(required=True)
    
    def validate_driver_id(self, value):
        if not User.objects.filter(id=value, role=User.Role.DRIVER).exists():
            raise serializers.ValidationError("A valid driver ID with the DRIVER role is required.")
        return value


class UpdateStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Shipment.Status.choices, required=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


# Backward compatibility alias
UpdateStatusSerializers = UpdateStatusSerializer