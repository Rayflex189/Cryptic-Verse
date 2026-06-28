from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvestmentPlanViewSet, InvestmentViewSet

router = DefaultRouter()
router.register(r'investment-plans', InvestmentPlanViewSet, basename='investmentplan')
router.register(r'investments', InvestmentViewSet, basename='investment')

urlpatterns = [
    path('', include(router.urls)),
]
