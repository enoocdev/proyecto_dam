# Rutas de la API REST de dispositivos aulas equipos de red y hosts permitidos
from rest_framework import routers
from django.urls import path, include
from .views import DevicesViewSet, ClassroomViewSet, NetworkDevicViewSet, ReadOnlyClassRoomWithoutPagination, AllowedHostViewSet


router = routers.DefaultRouter()

router.register(r'devices', DevicesViewSet, basename='device')
router.register(r"network-device", NetworkDevicViewSet, basename="network-device")
router.register(r'classroom', ClassroomViewSet, basename='classroom')
router.register(r'classroom-without-pagination', ReadOnlyClassRoomWithoutPagination, basename='classroom-without-pagination')
router.register(r'allowed-hosts', AllowedHostViewSet, basename='allowed-host')


urlpatterns = router.urls
