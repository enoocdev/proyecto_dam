from rest_framework import routers
from django.urls import path, include
from .views import UserViewSet, UserPermissionsView, UserGroupView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


router = routers.DefaultRouter()

router.register(r'users', UserViewSet, 'user')
router.register(r'permissions', UserPermissionsView, 'permission')
router.register(r'users-groups', UserGroupView, 'user-group')


urlpatterns = [
    path( '',  include(router.urls)),
    path('token/', TokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('auth/', include('rest_framework.urls')),
]

