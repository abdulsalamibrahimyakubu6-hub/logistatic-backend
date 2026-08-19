from rest_framework import serializers
from.models import User, Shipment, ShipmentStatusLog


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'phone_number']
        
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    
class ShipmentStatusLogSerializer(serializers.ModelSerializer):
    updated_by = serializers.StringRelatedField(read_only = True)
    
    class Meta:
        model = ShipmentStatusLog
        fields = ['status', 'updated_by', 'notes', 'timestamp']
        
class ShipmentSerializer(serializers.ModelSerializer):
    customer = serializers.StringRelatedField(read_only = True)
    driver = serializers.StringRelatedField(read_only = True)
    status_logs = ShipmentStatusLogSerializer(many = True, read_only = True)
    
    class Meta:
        model = Shipment
        fields = '__all__'
        read_only_fields = ['tracking_number', 'customer', 'driver','status', 'created_at']
        
class AssignDriverSerializer(serializers.Serializer):
    driver_id = serializers.IntegerField()
    
def validate_driver_id(self, value):
    if not User.objects.filter(id = value, role = User.Role.Driver).exists():
        raise serializers.ValidationError("valid driver ID required.")
    return value

class UpdateStatusSerializers(serializers.Serializer):
    status = serializers.ChoiceField(choices=Shipment.Status.choices)
    notes = serializers.CharField(required = False, allow_blank = True)