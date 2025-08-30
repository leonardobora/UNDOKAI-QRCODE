# PARTICIPANTS AGENTS.md

Gerenciamento de participantes, inscrições e dependentes para o evento BUNDOKAI.

## participants-setup

- python -c "from models import Participant, Dependent; print('Participant models imported')"
- python scripts/create_registration_form.py
- python scripts/setup_excel_import.py

## participants-import

- python scripts/import_excel.py --file=static/uploads/participants.xlsx
- python -c "from app import app, db, Participant; app.app_context().push(); print(f'Imported participants: {Participant.query.count()}')"
- python scripts/validate_imported_data.py

## participants-register

- python -c "from models import Participant; print('Registration form available at: /register')"
- python scripts/send_registration_emails.py
- python scripts/generate_registration_stats.py

## participants-qr

- python scripts/generate_qr_codes.py --batch-size=100
- python -c "import os; qr_count = len([f for f in os.listdir('static/qr_codes') if f.endswith('.png')]); print(f'QR codes generated: {qr_count}')"
- python scripts/validate_qr_codes.py

## participants-email

- python scripts/send_qr_codes_email.py --days-before=7
- python scripts/send_reminder_emails.py --days-before=1
- python scripts/track_email_delivery.py

## participants-verify

- python -c "from app import app, db, Participant, Dependent; app.app_context().push(); participants = Participant.query.count(); dependents = Dependent.query.count(); print(f'Total: {participants} participants, {dependents} dependents')"
- python scripts/check_duplicate_registrations.py
- python scripts/validate_participant_data.py

## participants-export

- python scripts/export_participants_excel.py
- python scripts/generate_checkin_lists.py
- python scripts/create_badges_pdf.py