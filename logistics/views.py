from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User, Shipment, ShipmentStatusLog
from .serializers import UserSerializer, ShipmentStatusLog, AssignDriverSerializer, ShipmentSerializer, UpdateStatusSerializers
from .permissions import IsAdmin, IsShipmentOwnerOrAdmin

# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    # def get_permissions(self):
    #     if self.action == "create" or self.request.method == 'POST':
    #         return [AllowAny()]
    #     return [IsAdmin()]
    def get_permissions(self):
        return [AllowAny()]


class ShipmentViewSet(viewsets.ModelViewSet):
    serializer_class = ShipmentSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        user = self.request.user
        #if user.role == User.Role.ADMIN:
        return Shipment.objects.all()
        #elif user.role == User.Role.DRIVER:
            #return Shipment.objects.filter(driver=user)
        #return Shipment.objects.filter(custom=user)
    
    def perform_create(self, serializer):
        #user=self.request.user if self.request.user.is_authenticated else User.objects.first()
        if self.request.user and self.request.user.is_authenticated:
            user = self.request.user
        else:
            user = User.objects.first()
        
        shipment = serializer.save(customer=user)
        ShipmentStatusLog.objects.create(
            shipment = shipment,
            status = Shipment.Status.PENDING,
            updated_by =user,
            notes = "order placed by customer."
        )
        
    @action(detail=True, methods=['patch'], permission_classes=[AllowAny])
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
            updated_by=request.user,
            notes=f"Driver {driver.username} assigned."
        )
        return Response(ShipmentSerializer(shipment).data)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        shipment = self.get_object()
        serializer = UpdateStatusSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        
        shipment.status = new_status
        shipment.save()
        
        ShipmentStatusLog.objects.create(
            shipment=shipment,
            status=new_status,
            updated_by=request.user,
            notes=notes
        )
        return Response(ShipmentSerializer(shipment).data)
    
class PublicTrackingViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [AllowAny]
    lookup_field = 'tracking_number'




# Create your views here.
