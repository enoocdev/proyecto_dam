from rest_framework import routers
from django.urls import path, include
from .views import DevicesViewSet, DeviceGroupViewSet, UserViewSet, UserGoupView


router = routers.DefaultRouter()

router.register(r'devices', DevicesViewSet, basename='device')
router.register(r'devices-groups', DeviceGroupViewSet, basename='device-group')

router.register(r'users', UserViewSet, 'user')
router.register(r'user-groups', UserGoupView, 'user-groups')


urlpatterns = router.urls
