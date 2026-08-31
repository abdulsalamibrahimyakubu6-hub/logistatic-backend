from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User, Shipment, ShipmentStatusLog
from .serializers import (
    UserSerializer,
    ShipmentStatusLogSerializer,
    AssignDriverSerializer,
    ShipmentSerializer,
    UpdateStatusSerializer,
)
from .permissions import IsAdmin, IsShipmentOwnerOrAdmin, IsAdminOrAssignedDriver


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        if user.role == User.Role.ADMIN or user.is_staff or user.is_superuser:
            return User.objects.all()
        # Non-admins can view their own profile and available drivers
        if self.action == 'list':
            return User.objects.filter(role=User.Role.DRIVER) | User.objects.filter(id=user.id)
        return User.objects.filter(id=user.id)

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        if request.method == 'PATCH':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(self.get_serializer(request.user).data)


class ShipmentViewSet(viewsets.ModelViewSet):
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Shipment.objects.none()
        if user.role == User.Role.ADMIN or user.is_staff or user.is_superuser:
            return Shipment.objects.all()
        elif user.role == User.Role.DRIVER:
            return Shipment.objects.filter(driver=user)
        return Shipment.objects.filter(customer=user)
    
    def perform_create(self, serializer):
        user = self.request.user
        shipment = serializer.save(customer=user)
        ShipmentStatusLog.objects.create(
            shipment=shipment,
            status=Shipment.Status.PENDING,
            updated_by=user if user.is_authenticated else None,
            notes="Order placed by customer."
        )
        
    @action(detail=True, methods=['patch'], permission_classes=[IsAdmin])
    def assign_driver(self, request, pk=None):
        shipment = self.get_object()
        serializer = AssignDriverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        driver = User.objects.get(id=serializer.validated_data['driver_id'])
        shipment.driver = driver
        shipment.status = Shipment.Status.ASSIGNED
        shipment.save()
        
        ShipmentStatusLog.objects.create(
            shipment=shipment,
            status=Shipment.Status.ASSIGNED,
            updated_by=request.user if request.user.is_authenticated else None,
            notes=f"Driver {driver.username} assigned."
        )
        return Response(ShipmentSerializer(shipment).data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminOrAssignedDriver])
    def update_status(self, request, pk=None):
        shipment = self.get_object()
        serializer = UpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        
        shipment.status = new_status
        shipment.save()
        
        ShipmentStatusLog.objects.create(
            shipment=shipment,
            status=new_status,
            updated_by=request.user if request.user.is_authenticated else None,
            notes=notes
        )
        return Response(ShipmentSerializer(shipment).data)


class PublicTrackingViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [AllowAny]
    lookup_field = 'tracking_number'
