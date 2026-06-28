from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepositViewSet

router = DefaultRouter()
router.register(r'deposits', DepositViewSet, basename='deposit')

urlpatterns = [
    path('', include(router.urls)),
]
