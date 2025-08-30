# AGENTS.md - LIGHTERA BUNDOKAI SYSTEM

Sistema de check-in e controle de entregas para eventos corporativos da Lightera/Furukawa Electric.
Substitui solução Digitevent (R$ 5.427,00) com funcionalidades essenciais para até 2500 participantes.

## setup

- python3 --version
- python3 -m venv venv --prompt="lightera-bundokai"
- source venv/bin/activate
- python -m pip install --upgrade pip setuptools wheel
- pip install Flask==2.3.3 Flask-SQLAlchemy==3.0.5 qrcode[pil]==7.4.2 pandas==2.1.1 gunicorn==21.2.0 python-dotenv==1.0.0 Pillow==10.0.1 opencv-python-headless==4.8.1.78
- cp .env.example .env
- python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"
- mkdir -p static/qr_codes static/uploads logs reports static/checkin_cache
- python scripts/setup_database.py

## test

- python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing
- python -c "import requests; r = requests.get('http://localhost:5000/health', timeout=5); print(f'Health check: {r.status_code}' if r.status_code == 200 else 'Health check failed')"
- python -c "from models import Participant, CheckIn, DeliveryItem; print('Models imported successfully')"
- python -c "from utils import generate_qr_code; qr = generate_qr_code('TEST123'); print('QR generation working')"

## lint

- python -m flake8 app.py models.py routes.py utils.py --max-line-length=88 --statistics
- python -m py_compile app.py models.py routes.py utils.py
- python -c "import app, models, routes, utils; print('All modules compile successfully')"

## build

- python -c "import qrcode, PIL, flask, flask_sqlalchemy, pandas; print('Dependencies OK')"
- python scripts/generate_sample_data.py
- python -c "from utils import create_sample_delivery_items; create_sample_delivery_items(); print('Sample data created')"
- chmod +x run.sh

## run

- export FLASK_ENV=development
- export FLASK_DEBUG=True
- python app.py

## deploy

- export FLASK_ENV=production
- export DATABASE_URL=sqlite:///bundokai_prod.db
- gunicorn --workers=4 --bind=0.0.0.0:5000 app:app

## cleanup

- find . -name "*.pyc" -delete
- find . -name "__pycache__" -type d -exec rm -rf {} +
- rm -rf static/qr_codes/*.png
- rm -rf static/uploads/*.xlsx
- rm -rf logs/*.log

## backup

- cp bundokai.db backups/bundokai_$(date +%Y%m%d_%H%M%S).db
- python -c "from app import app, db; from models import *; app.app_context().push(); print(f'Participants: {Participant.query.count()}, Check-ins: {CheckIn.query.count()}')"
- tar -czf backups/static_$(date +%Y%m%d_%H%M%S).tar.gz static/

## monitor

- python -c "from app import app; app.app_context().push(); print('Application health: OK')"
- python -c "import psutil; print(f'Memory usage: {psutil.virtual_memory().percent}%')"
- python -c "import os; print(f'Database size: {os.path.getsize("bundokai.db") / 1024 / 1024:.2f} MB')"
- tail -f logs/app.log

## stats

- python -c "from app import app, db; from models import *; app.app_context().push(); participants = Participant.query.count(); checkins = CheckIn.query.count(); print(f'Total participants: {participants}'); print(f'Total check-ins: {checkins}'); print(f'Attendance rate: {(checkins/participants*100):.1f}%' if participants > 0 else 'No participants yet')"
- python -c "from datetime import datetime; print(f'System status checked at: {datetime.now().isoformat()}')"
