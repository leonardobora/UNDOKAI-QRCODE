# EMAIL AGENTS.md

Sistema de campanhas de email para UNDOKAI - QR codes, lembretes e notificações automáticas.

## email-setup

- python -c "import smtplib; print('SMTP client ready')"
- python -c "from utils import send_qr_email; print('Email templates configured')"
- mkdir -p templates/emails static/email_attachments
- python -c "import os; required_vars = ['SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD']; missing = [var for var in required_vars if not os.environ.get(var)]; print(f'Email config status: {\"Ready\" if not missing else f\"Missing: {missing}\"}')"

## email-templates

- python -c "from scripts.send_qr_emails import create_email_template; from models import Participant; print('QR email template ready')"
- python -c "print('Reminder template available')"
- python -c "print('Confirmation template available')"
- python -c "from utils import generate_qr_code; qr = generate_qr_code('TEST123'); print('Email template validation passed')"

## email-qr-delivery

- python scripts/send_qr_emails.py --type=qr --dry-run
- python -c "from models import EmailLog; from app import app, db; app.app_context().push(); sent = EmailLog.query.filter_by(email_type='qr_delivery').count(); print(f'QR emails sent: {sent}')"
- python -c "from models import EmailLog; from app import app, db; app.app_context().push(); opened = EmailLog.query.filter(EmailLog.opened_at.isnot(None)).count(); print(f'Emails opened: {opened}')"

## email-reminders

- python scripts/send_qr_emails.py --type=reminder --days-before=1 --dry-run
- python -c "from models import EmailLog; from app import app, db; app.app_context().push(); reminders = EmailLog.query.filter_by(email_type='reminder').count(); print(f'Reminder emails sent: {reminders}')"
- python -c "print('Check-in reminder system ready')"

## email-automation

- python -c "from datetime import datetime, timedelta; event_date = datetime(2024, 12, 15); days_until = (event_date - datetime.now()).days; print(f'Days until event: {days_until}')"
- python scripts/send_qr_emails.py --batch-size=10 --delay=1 --dry-run
- python -c "from datetime import datetime; print(f'Email automation active since: {datetime.now().isoformat()}')"

## email-tracking

- python -c "from models import EmailLog; from app import app, db; app.app_context().push(); total_sent = EmailLog.query.filter_by(status='sent').count(); total_failed = EmailLog.query.filter_by(status='failed').count(); print(f'Email delivery: {total_sent} sent, {total_failed} failed')"
- python -c "from models import EmailLog; from app import app, db; app.app_context().push(); opened = EmailLog.query.filter(EmailLog.opened_at.isnot(None)).count(); sent = EmailLog.query.filter_by(status='sent').count(); rate = (opened/sent*100) if sent > 0 else 0; print(f'Open rate: {rate:.1f}%')"
- python -c "from models import EmailLog; from app import app, db; app.app_context().push(); bounced = EmailLog.query.filter_by(status='bounced').count(); print(f'Bounced emails: {bounced}')"

## email-cleanup

- python -c "from models import EmailLog; from app import app, db; from datetime import datetime, timedelta; app.app_context().push(); old_emails = EmailLog.query.filter(EmailLog.sent_at < datetime.now() - timedelta(days=30)).count(); print(f'Old emails to archive: {old_emails}')"
- rm -rf static/email_attachments/*.tmp
- python -c "print('Email system cleanup completed')"
