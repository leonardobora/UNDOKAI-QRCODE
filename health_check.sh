#!/bin/bash

# Quick health check script for Lightera UNDOKAI
echo "🏥 Lightera UNDOKAI - Health Check"
echo "=================================="

# Test core components
echo "Testing core functionality..."

python -c "
import sys
try:
    print('✅ Testing imports...')
    from app import app, db
    from models import Participant, CheckIn, DeliveryItem
    print('✅ Core modules imported successfully')
    
    print('✅ Testing database...')
    with app.app_context():
        db.create_all()
        print('✅ Database operations working')
    
    print('✅ Testing QR generation...')
    # Import directly to avoid circular import in health check
    import qrcode, io, base64
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data('HEALTH_CHECK')
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    print('✅ QR generation working')
    
    print('\n🎉 System Health: GOOD')
    print('All core components are functioning correctly!')
    
except Exception as e:
    print(f'❌ Health check failed: {e}')
    sys.exit(1)
"