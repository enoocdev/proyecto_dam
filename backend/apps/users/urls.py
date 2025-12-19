from rest_framework import routers
from django.urls import path, include
from .views import UserViewSet, UserPermissionsView, UserGroupView, CustomTokenObtainPairView, ReadOnlyGroupWithoutPagination
from rest_framework_simplejwt.views import TokenRefreshView


router = routers.DefaultRouter()

router.register(r'users', UserViewSet, 'user')
router.register(r'permissions', UserPermissionsView, 'permission')
router.register(r'users-groups', UserGroupView, 'user-group')
router.register(r'users-groups-without-pagination', ReadOnlyGroupWithoutPagination, 'users-groups-without-pagination')


urlpatterns = [
    path( '',  include(router.urls)),
    path('token/',  CustomTokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('auth/', include('rest_framework.urls')),
]

