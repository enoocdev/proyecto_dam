from rest_framework import routers
from .views import DevicesViewSet, GroupViewSet


router = routers.DefaultRouter()

router.register('devices', DevicesViewSet, 'devices')
router.register('groups', GroupViewSet, 'groups')

urlpatterns = router.urls