from rest_framework import routers
from .views import DevicesViewSet, GroupViewSet


router = routers.DefaultRouter()

router.register(r'devices', DevicesViewSet, 'device')
router.register(r'groups', GroupViewSet, 'group')

urlpatterns = router.urls