from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import get_market_data, get_public_settings, convert_balance

urlpatterns = [
    path('django-admin/', admin.site.urls),
    
    path('api/v1/', include([
        path('market-data/', get_market_data, name='market_data'),
        path('website-settings/', get_public_settings, name='public_settings'),
        path('convert-balance/', convert_balance, name='convert_balance'),
        
        path('', include('users.urls')),
        path('', include('wallets.urls')),
        path('', include('deposits.urls')),
        path('', include('withdrawals.urls')),
        path('', include('investments.urls')),
        path('', include('kyc.urls')),
        path('', include('transactions.urls')),
        path('', include('notifications.urls')),
        path('', include('support.urls')),
        path('admin/', include('admin_panel.urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
