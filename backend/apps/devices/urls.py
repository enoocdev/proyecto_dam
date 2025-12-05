from rest_framework import routers
from django.urls import path, include
from .views import DevicesViewSet, DeviceGroupViewSet


router = routers.DefaultRouter()

router.register(r'devices', DevicesViewSet, basename='device')
router.register(r'devices-groups', DeviceGroupViewSet, basename='device-group')


urlpatterns = router.urls
