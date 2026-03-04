from rest_framework import routers
from django.urls import path, include
from .views import DevicesViewSet, ClassroomViewSet, NetworkDevicViewSet, ReadOnlyDeviceWithoutPagination


router = routers.DefaultRouter()

router.register(r'devices', DevicesViewSet, basename='device')
router.register(r"network-device", NetworkDevicViewSet, basename="network-device")
router.register(r'classroom', ClassroomViewSet, basename='classroom')
router.register(r'devices-without-pagination', ReadOnlyDeviceWithoutPagination, basename='devices-without-pagination')


urlpatterns = router.urls
