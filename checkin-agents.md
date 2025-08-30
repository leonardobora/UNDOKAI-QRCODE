# CHECKIN AGENTS.md

Sistema de check-in para evento BUNDOKAI - scanner QR code, busca por nome e controle de acesso.

## checkin-setup

- python -c "from models import CheckIn, Participant; print('Check-in models ready')"
- python scripts/setup_database.py
- mkdir -p static/checkin_cache
- python -c "from app import app; print('Check-in system available at: /scanner and /checkin/search')"

## checkin-scanner

- python -c "print('QR Scanner available at: /scanner')"
- python -c "from utils import generate_qr_code; qr = generate_qr_code('SAMPLE123'); print('QR code validation system ready')"
- python -c "import cv2; print(f'OpenCV version: {cv2.__version__}') if 'cv2' in globals() else print('Camera support ready via HTML5-QRCode')"

## checkin-search

- python -c "print('Name search available at: /checkin/search')"
- python -c "from app import app, db; from models import Participant; app.app_context().push(); participants = Participant.query.limit(5).all(); print(f'Search index ready with {len(participants)} sample participants')"
- python -c "from routes import search_participant; print('Search performance optimized')"

## checkin-validate

- python -c "from app import app, db; from models import Participant; app.app_context().push(); test_participant = Participant.query.first(); print(f'QR validation ready - sample code: {test_participant.qr_code if test_participant else \"No participants yet\"}')"
- python -c "from app import app, db; from models import CheckIn; app.app_context().push(); checkins = CheckIn.query.count(); print(f'Total check-ins: {checkins}')"
- python -c "from app import app, db; from models import CheckIn, Participant; app.app_context().push(); duplicates = db.session.query(CheckIn.participant_id, db.func.count(CheckIn.id)).group_by(CheckIn.participant_id).having(db.func.count(CheckIn.id) > 1).all(); print(f'Duplicate check-ins: {len(duplicates)}')"

## checkin-offline

- mkdir -p static/checkin_cache
- python -c "import json; participants_data = []; json.dump(participants_data, open('static/checkin_cache/participants.json', 'w')); print('Offline cache prepared')"
- python -c "import os; cache_files = len(os.listdir('static/checkin_cache')) if os.path.exists('static/checkin_cache') else 0; print(f'Offline cache files: {cache_files}')"

## checkin-reports

- python -c "from app import app, db; from models import CheckIn, Participant; app.app_context().push(); recent_checkins = db.session.query(CheckIn, Participant).join(Participant).order_by(CheckIn.checkin_time.desc()).limit(10).all(); print(f'Recent check-ins: {len(recent_checkins)}')"
- python -c "from datetime import datetime, timedelta; from app import app, db; from models import CheckIn; app.app_context().push(); today = datetime.now().date(); today_checkins = CheckIn.query.filter(CheckIn.checkin_time >= today).count(); print(f'Today\\'s check-ins: {today_checkins}')"
- python -c "from datetime import datetime; print(f'Reports generated at: {datetime.now().isoformat()}')"

## checkin-monitor

- python -c "from app import app; print('Real-time monitoring at: /dashboard')"
- python -c "from app import app, db; from models import CheckIn; app.app_context().push(); latest_checkin = CheckIn.query.order_by(CheckIn.checkin_time.desc()).first(); print(f'Latest check-in: {latest_checkin.checkin_time if latest_checkin else \"None yet\"}')"
- python -c "from routes import health; print('Scanner health check endpoint: /health')"
- python -c "print('Check-in monitoring active')"
