from django.urls import path, include
from .views import *
from .auth import AuthenticationViewSet

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'auth', AuthenticationViewSet, basename='auth')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
