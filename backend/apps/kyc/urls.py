from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KYCDocumentViewSet, KYCStatusView

router = DefaultRouter()
router.register(r'kyc/documents', KYCDocumentViewSet, basename='kycdocuments')

urlpatterns = [
    path('kyc/status/', KYCStatusView.as_view(), name='kyc_status'),
    path('', include(router.urls)),
]
