# Rutas de la API REST de dispositivos aulas y equipos de red
from rest_framework import routers
from django.urls import path, include
from .views import DevicesViewSet, ClassroomViewSet, NetworkDevicViewSet, ReadOnlyClassRoomWithoutPagination


router = routers.DefaultRouter()

router.register(r'devices', DevicesViewSet, basename='device')
router.register(r"network-device", NetworkDevicViewSet, basename="network-device")
router.register(r'classroom', ClassroomViewSet, basename='classroom')
router.register(r'classroom-without-pagination', ReadOnlyClassRoomWithoutPagination, basename='classroom-without-pagination')


urlpatterns = router.urls
