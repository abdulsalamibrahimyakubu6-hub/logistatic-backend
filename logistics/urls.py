from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserViewSet, ShipmentViewSet, PublicTrackingViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'shipment', ShipmentViewSet, basename='shipment')
router.register(r'track', PublicTrackingViewSet, basename='track')

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh', TokenRefreshView.as_view, name='token_refresh'),

    path('', include(router.urls)),
]