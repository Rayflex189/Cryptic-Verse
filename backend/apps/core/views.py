import random
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin_panel.models import WebsiteSetting

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_market_data(request):
    # Return mock cryptocurrency prices with slight random variations to simulate live tickers
    base_prices = {
        'BTC': 65230.50,
        'ETH': 3450.25,
        'USDT': 1.00,
        'BNB': 585.10,
        'SOL': 145.75
    }
    
    data = []
    for crypto, price in base_prices.items():
        # Add a random daily change between -3% and +3%
        change_pct = random.uniform(-3.5, 3.5) if crypto != 'USDT' else 0.00
        price_adjusted = price * (1 + change_pct / 100) if crypto != 'USDT' else 1.00
        data.append({
            'symbol': crypto,
            'name': 'Tether' if crypto == 'USDT' else crypto,
            'price': round(price_adjusted, 2),
            'change_24h': round(change_pct, 2)
        })
    return Response(data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_public_settings(request):
    # Fetch public settings
    settings_qs = WebsiteSetting.objects.filter(category='general')
    settings_dict = {}
    for s in settings_qs:
        settings_dict[s.key] = s.value
        
    # Default values if empty
    defaults = {
        'company_name': 'Cryptic Verse',
        'support_email': 'support@crypticverse.com',
        'footer_text': '© 2026 Cryptic Verse Platform. All rights reserved.',
        'contact_phone': '+1 (800) 555-0199',
    }
    
    for k, v in defaults.items():
        if k not in settings_dict:
            settings_dict[k] = v
            
    return Response(settings_dict)

from django.db import transaction as db_transaction
from decimal import Decimal
from .models import CompanyWallet, PlatformSetting
from wallets.models import Wallet
from transactions.models import Transaction

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_company_wallet(request):
    wallet = CompanyWallet.objects.filter(is_active=True).first()
    settings_obj = PlatformSetting.get_settings()
    
    if wallet:
        return Response({
            'wallet_name': wallet.wallet_name,
            'wallet_address': wallet.wallet_address,
            'network': wallet.network,
            'is_active': wallet.is_active
        })
    else:
        return Response({
            'wallet_name': 'Company Wallet',
            'wallet_address': settings_obj.company_wallet_address,
            'network': settings_obj.wallet_network,
            'is_active': True
        })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_platform_settings(request):
    settings_obj = PlatformSetting.get_settings()
    return Response({
        'vip_upgrade_fee': float(settings_obj.vip_upgrade_fee),
        'company_wallet_address': settings_obj.company_wallet_address,
        'wallet_network': settings_obj.wallet_network,
        'conversion_fee_pct': float(settings_obj.conversion_fee_pct),
        'enable_currency_converter': settings_obj.enable_currency_converter,
        'enable_vip_upgrade': settings_obj.enable_vip_upgrade,
        'enable_withdrawals': settings_obj.enable_withdrawals
    })

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def convert_balance(request):
    settings_obj = PlatformSetting.get_settings()
    if not settings_obj.enable_currency_converter:
        return Response({'error': 'Currency converter is currently disabled by administrator.'}, status=status.HTTP_400_BAD_REQUEST)

    rates = {
        'BTC': 65230.50,
        'ETH': 3450.25,
        'USDT': 1.00,
        'BNB': 585.10,
        'SOL': 145.75,
        'EUR': 0.92,
        'GBP': 0.79,
    }

    if request.method == 'GET':
        target_currency = request.query_params.get('target_currency', 'BTC').upper()
        if target_currency not in rates:
            return Response({'error': f'Unsupported currency: {target_currency}'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = request.user
        balance = float(user.balance)
        fee_pct = float(settings_obj.conversion_fee_pct)
        
        # Calculate fee
        fee_amount = balance * (fee_pct / 100.0)
        net_balance = balance - fee_amount
        rate = rates[target_currency]
        
        if target_currency in ['BTC', 'ETH', 'BNB', 'SOL']:
            converted_amount = net_balance / rate
        else:
            converted_amount = net_balance * rate
            
        return Response({
            'balance_usdt': balance,
            'fee_pct': fee_pct,
            'fee_amount': round(fee_amount, 2),
            'net_balance_usdt': round(net_balance, 2),
            'target_currency': target_currency,
            'rate': rate,
            'converted_amount': round(converted_amount, 6)
        })

    elif request.method == 'POST':
        amount_raw = request.data.get('amount')
        target_currency = request.data.get('target_currency', 'BTC').upper()

        if not amount_raw or float(amount_raw) <= 0:
            return Response({'error': 'Please enter a valid positive conversion amount.'}, status=status.HTTP_400_BAD_REQUEST)

        if target_currency not in rates:
            return Response({'error': f'Unsupported target currency: {target_currency}'}, status=status.HTTP_400_BAD_REQUEST)

        amount = Decimal(str(amount_raw))
        user = request.user

        if user.balance < amount:
            return Response({'error': f'Insufficient available balance. Your USDT balance is ${float(user.balance):.2f}'}, status=status.HTTP_400_BAD_REQUEST)

        fee_pct = Decimal(str(settings_obj.conversion_fee_pct))
        fee_amount = amount * (fee_pct / Decimal('100.0'))
        net_amount = amount - fee_amount

        rate_val = Decimal(str(rates[target_currency]))
        if target_currency in ['BTC', 'ETH', 'BNB', 'SOL']:
            received_amount = net_amount / rate_val
        else:
            received_amount = net_amount * rate_val

        with db_transaction.atomic():
            # Deduct USDT balance from user
            user.balance -= amount
            user.save(update_fields=['balance'])

            # Credit target wallet
            target_wallet, _ = Wallet.objects.get_or_create(user=user, currency=target_currency)
            target_wallet.balance += received_amount
            target_wallet.save(update_fields=['balance'])

            # Record transaction in history
            tx_desc = f"Currency Conversion | From: {amount:.2f} USDT | Fee: {fee_amount:.2f} USDT | Converted: {net_amount:.2f} USDT | Received: {received_amount:.6f} {target_currency}"
            Transaction.objects.create(
                user=user,
                wallet=target_wallet,
                type='ADMIN_ADJUSTMENT',
                amount=received_amount,
                currency=target_currency,
                description=tx_desc,
                status='COMPLETED'
            )

        return Response({
            'message': f'Successfully converted ${float(amount):.2f} USDT to {float(received_amount):.6f} {target_currency}.',
            'from_amount': float(amount),
            'fee_amount': float(fee_amount),
            'converted_amount': float(net_amount),
            'received_amount': float(received_amount),
            'target_currency': target_currency,
            'new_usdt_balance': float(user.balance),
            'new_target_balance': float(target_wallet.balance)
        })

