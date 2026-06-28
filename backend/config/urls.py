from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.views.generic import TemplateView
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

# Path to React built dist
FRONTEND_DIST = settings.BASE_DIR.parent / 'frontend' / 'dist'

urlpatterns += [
    # Serve assets folder
    re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': FRONTEND_DIST / 'assets'}),
    # Serve root level static files (favicon.svg, manifest.json, sw.js, etc.)
    re_path(r'^(?P<path>(?:favicon\.svg|manifest\.json|sw\.js|logo\.png|favicon\.ico))$', serve, {'document_root': FRONTEND_DIST}),
    # Catch-all: serve React index.html for all other routes
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html'), name='index'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
