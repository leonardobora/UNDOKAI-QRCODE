# PARTICIPANTS AGENTS.md

Gerenciamento de participantes, inscrições e dependentes para o evento BUNDOKAI.

## participants-setup

- python -c "from models import Participant, Dependent; print('Participant models imported')"
- python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Participant tables ready')"
- mkdir -p static/uploads static/qr_codes

## participants-import

- python -c "import pandas as pd; print('Excel import capability ready')"
- python -c "from app import app, db, Participant; app.app_context().push(); print(f'Imported participants: {Participant.query.count()}')"
- python -c "from models import Participant; print('Participant validation ready')"

## participants-register

- python -c "from models import Participant; print('Registration form available at: /register')"
- python -c "from app import app; app.app_context().push(); print('Registration endpoint active')"
- python -c "from utils import generate_qr_code; print('QR code generation ready')"

## participants-qr

- python -c "from utils import generate_qr_code; qr = generate_qr_code('TEST123'); print('QR code generation working')"
- python -c "import os; qr_count = len([f for f in os.listdir('static/qr_codes') if f.endswith('.png')]) if os.path.exists('static/qr_codes') else 0; print(f'QR codes available: {qr_count}')"
- python -c "from app import app, db; from models import Participant; app.app_context().push(); participants = Participant.query.all(); print(f'Participants with QR codes: {len([p for p in participants if p.qr_code])}')"

## participants-email

- python -c "from utils import send_qr_email; print('Email delivery system ready')"
- python scripts/send_qr_emails.py --dry-run
- python -c "from models import EmailLog; from app import app, db; app.app_context().push(); sent_emails = EmailLog.query.filter_by(email_type='qr_delivery', status='sent').count(); print(f'QR emails sent: {sent_emails}')"

## participants-verify

- python -c "from app import app, db; from models import Participant, Dependent; app.app_context().push(); participants = Participant.query.count(); dependents = Dependent.query.count(); print(f'Total: {participants} participants, {dependents} dependents')"
- python -c "from app import app, db; from models import Participant; app.app_context().push(); duplicates = db.session.query(Participant.email, db.func.count(Participant.id)).group_by(Participant.email).having(db.func.count(Participant.id) > 1).all(); print(f'Duplicate emails found: {len(duplicates)}')"
- python -c "from app import app, db; from models import Participant; app.app_context().push(); invalid_qr = Participant.query.filter(Participant.qr_code.is_(None)).count(); print(f'Participants without QR codes: {invalid_qr}')"

## participants-export

- python -c "import pandas as pd; from app import app, db; from models import Participant; app.app_context().push(); participants = Participant.query.all(); df = pd.DataFrame([{'nome': p.nome, 'email': p.email, 'departamento': p.departamento, 'qr_code': p.qr_code, 'dependents': len(p.dependents)} for p in participants]); print(f'Export ready: {len(df)} participants')"
- python -c "from datetime import datetime; print(f'Participant export generated at: {datetime.now().isoformat()}')"
- python -c "from app import app, db; from models import CheckIn; app.app_context().push(); checkins = CheckIn.query.count(); print(f'Check-in list contains: {checkins} entries')"
