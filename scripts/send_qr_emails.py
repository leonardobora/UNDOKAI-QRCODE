#!/usr/bin/env python3
"""
Send QR Code Emails to Participants
Batch email sending for BUNDOKAI event participants
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import base64
import logging
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.image import MimeImage
from email.mime.multipart import MimeMultipart
from email.mime.text import MimeText

from app import app, db
from models import EmailLog, Participant
from utils import generate_qr_code, send_qr_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_email_config():
    """Validate email configuration"""
    required_vars = ["SMTP_SERVER", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD"]
    missing_vars = []

    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing email configuration: {', '.join(missing_vars)}")
        logger.info("Please set the following environment variables:")
        for var in missing_vars:
            logger.info(f"  {var}=your_value")
        return False

    return True


def create_email_template(participant, qr_image_data):
    """Create HTML email template"""
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #6f42c1, #5a359a);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f8f9fa;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .qr-container {{
                text-align: center;
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .qr-code {{
                max-width: 200px;
                height: auto;
            }}
            .info-box {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                border-left: 4px solid #6f42c1;
            }}
            .footer {{
                text-align: center;
                color: #666;
                font-size: 12px;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }}
            .btn {{
                display: inline-block;
                background: #6f42c1;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 5px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎉 BUNDOKAI 2024</h1>
            <p>Seu QR Code de Acesso</p>
        </div>
        
        <div class="content">
            <h2>Olá, {participant.nome}! 👋</h2>
            
            <p>Sua inscrição para o <strong>BUNDOKAI 2024</strong> foi confirmada com sucesso!</p>
            
            <div class="qr-container">
                <h3>Seu QR Code de Acesso</h3>
                <img src="data:image/png;base64,{qr_image_data}" alt="QR Code" class="qr-code">
                <p><strong>Código: {participant.qr_code}</strong></p>
                <p><small>Apresente este código na entrada do evento</small></p>
            </div>
            
            <div class="info-box">
                <h4>📋 Detalhes da sua Inscrição</h4>
                <p><strong>Nome:</strong> {participant.nome}</p>
                <p><strong>Email:</strong> {participant.email}</p>
                {f"<p><strong>Departamento:</strong> {participant.departamento}</p>" if participant.departamento else ""}
                <p><strong>Dependentes:</strong> {len(participant.dependents)} pessoa(s)</p>
                {f"<p><strong>Lista de Dependentes:</strong></p><ul>{''.join([f'<li>{dep.nome} ({dep.idade} anos)</li>' for dep in participant.dependents])}</ul>" if participant.dependents else ""}
            </div>
            
            <div class="info-box">
                <h4>📅 Informações do Evento</h4>
                <p><strong>Data:</strong> 15 de Dezembro de 2024</p>
                <p><strong>Local:</strong> Centro de Convenções Lightera</p>
                <p><strong>Horário:</strong> 14h00 às 18h00</p>
                <p><strong>Dress Code:</strong> Casual</p>
            </div>
            
            <div class="info-box">
                <h4>🎁 O que esperar?</h4>
                <ul>
                    <li>🍕 Festa com comidas e bebidas</li>
                    <li>🎮 Atividades para toda família</li>
                    <li>🎁 Distribuição de presentes</li>
                    <li>🏆 Sorteios especiais</li>
                    <li>📸 Espaço para fotos</li>
                </ul>
            </div>
            
            <div style="text-align: center;">
                <p><strong>⚠️ IMPORTANTE: Guarde este QR Code com cuidado!</strong></p>
                <p>Você precisará dele para:</p>
                <ul style="text-align: left;">
                    <li>✅ Fazer check-in na entrada do evento</li>
                    <li>🎁 Retirar presentes e kits</li>
                    <li>🍽️ Participar das atividades</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>Este email foi enviado automaticamente pelo sistema Lightera BUNDOKAI.</p>
            <p>Em caso de dúvidas, entre em contato conosco.</p>
            <p>&copy; 2024 Lightera / Furukawa Electric - Todos os direitos reservados</p>
        </div>
    </body>
    </html>
    """

    return html_template


def send_single_email(participant, dry_run=False):
    """Send QR code email to a single participant"""
    try:
        # Generate QR code
        qr_image = generate_qr_code(participant.qr_code)

        # Extract base64 data
        qr_base64 = qr_image.split(",")[1] if "," in qr_image else qr_image

        if dry_run:
            logger.info(
                f"[DRY RUN] Would send email to {participant.nome} ({participant.email})"
            )
            return True

        # Email configuration
        smtp_server = os.environ.get("SMTP_SERVER")
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        smtp_username = os.environ.get("SMTP_USERNAME")
        smtp_password = os.environ.get("SMTP_PASSWORD")

        # Create message
        msg = MimeMultipart("related")
        msg["From"] = smtp_username
        msg["To"] = participant.email
        msg["Subject"] = "BUNDOKAI 2024 - Seu QR Code de Acesso"

        # Create HTML body
        html_body = create_email_template(participant, qr_base64)
        msg.attach(MimeText(html_body, "html"))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        # Log email in database
        with app.app_context():
            email_log = EmailLog(
                participant_id=participant.id,
                email_type="qr_delivery",
                subject=msg["Subject"],
                status="sent",
            )
            db.session.add(email_log)
            db.session.commit()

        logger.info(f"✅ Email sent to {participant.nome} ({participant.email})")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email to {participant.nome}: {str(e)}")

        # Log failed email
        try:
            with app.app_context():
                email_log = EmailLog(
                    participant_id=participant.id,
                    email_type="qr_delivery",
                    subject="BUNDOKAI 2024 - Seu QR Code de Acesso",
                    status="failed",
                )
                db.session.add(email_log)
                db.session.commit()
        except:
            pass

        return False


def send_batch_emails(batch_size=10, delay=1, dry_run=False, filter_department=None):
    """Send emails in batches to avoid overwhelming SMTP server"""

    with app.app_context():
        # Get participants who haven't received QR emails yet
        query = (
            db.session.query(Participant)
            .outerjoin(
                EmailLog,
                (EmailLog.participant_id == Participant.id)
                & (EmailLog.email_type == "qr_delivery")
                & (EmailLog.status == "sent"),
            )
            .filter(EmailLog.id.is_(None))
        )

        # Filter by department if specified
        if filter_department:
            query = query.filter(Participant.departamento == filter_department)

        participants = query.all()

        if not participants:
            logger.info("No participants found who need QR code emails.")
            return True

        logger.info(f"Found {len(participants)} participants to send emails to")

        if dry_run:
            logger.info("DRY RUN MODE - No emails will actually be sent")

        success_count = 0
        error_count = 0

        # Process in batches
        for i in range(0, len(participants), batch_size):
            batch = participants[i : i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} emails")

            for participant in batch:
                success = send_single_email(participant, dry_run=dry_run)

                if success:
                    success_count += 1
                else:
                    error_count += 1

                # Small delay between emails
                if not dry_run:
                    time.sleep(delay)

            # Longer delay between batches
            if i + batch_size < len(participants):
                logger.info(f"Waiting {delay * 5} seconds before next batch...")
                if not dry_run:
                    time.sleep(delay * 5)

        logger.info(f"\n📊 Email sending completed!")
        logger.info(f"✅ Successful: {success_count}")
        logger.info(f"❌ Failed: {error_count}")
        logger.info(
            f"📈 Success rate: {(success_count / len(participants)) * 100:.1f}%"
        )

        return error_count == 0


def send_reminder_emails(days_before=1, dry_run=False):
    """Send reminder emails before the event"""

    with app.app_context():
        # Get all participants
        participants = Participant.query.all()

        if not participants:
            logger.info("No participants found.")
            return True

        logger.info(f"Sending reminder emails to {len(participants)} participants")

        success_count = 0
        error_count = 0

        for participant in participants:
            try:
                if dry_run:
                    logger.info(f"[DRY RUN] Would send reminder to {participant.nome}")
                    success_count += 1
                    continue

                # Email configuration
                smtp_server = os.environ.get("SMTP_SERVER")
                smtp_port = int(os.environ.get("SMTP_PORT", 587))
                smtp_username = os.environ.get("SMTP_USERNAME")
                smtp_password = os.environ.get("SMTP_PASSWORD")

                # Create reminder message
                msg = MimeMultipart()
                msg["From"] = smtp_username
                msg["To"] = participant.email
                msg["Subject"] = (
                    f"BUNDOKAI 2024 - Lembrete: Evento em {days_before} dia(s)!"
                )

                body = f"""
                Olá {participant.nome}!
                
                Este é um lembrete amigável sobre o BUNDOKAI 2024!
                
                📅 O evento acontece em {days_before} dia(s)
                🕐 Data: 15 de Dezembro de 2024
                🏢 Local: Centro de Convenções Lightera
                ⏰ Horário: 14h00 às 18h00
                
                🎫 Seu QR Code: {participant.qr_code}
                
                Não se esqueça de trazer seu QR Code para fazer o check-in!
                
                Nos vemos lá! 🎉
                
                Equipe Lightera
                """

                msg.attach(MimeText(body, "plain"))

                # Send email
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)

                # Log email
                email_log = EmailLog(
                    participant_id=participant.id,
                    email_type="reminder",
                    subject=msg["Subject"],
                    status="sent",
                )
                db.session.add(email_log)

                success_count += 1
                logger.info(f"✅ Reminder sent to {participant.nome}")

                time.sleep(0.5)  # Small delay

            except Exception as e:
                logger.error(
                    f"❌ Failed to send reminder to {participant.nome}: {str(e)}"
                )
                error_count += 1

        try:
            db.session.commit()
        except:
            pass

        logger.info(f"\n📊 Reminder emails completed!")
        logger.info(f"✅ Successful: {success_count}")
        logger.info(f"❌ Failed: {error_count}")

        return error_count == 0


def main():
    """Main email sending function"""
    parser = argparse.ArgumentParser(
        description="Send QR Code emails to BUNDOKAI participants"
    )
    parser.add_argument(
        "--type",
        choices=["qr", "reminder"],
        default="qr",
        help="Type of email to send (default: qr)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of emails per batch (default: 10)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between emails in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test run without actually sending emails",
    )
    parser.add_argument("--department", type=str, help="Filter by department")
    parser.add_argument(
        "--days-before",
        type=int,
        default=1,
        help="Days before event for reminder (default: 1)",
    )

    args = parser.parse_args()

    logger.info("Starting BUNDOKAI email sending...")

    # Validate email configuration
    if not args.dry_run and not validate_email_config():
        sys.exit(1)

    try:
        if args.type == "qr":
            success = send_batch_emails(
                batch_size=args.batch_size,
                delay=args.delay,
                dry_run=args.dry_run,
                filter_department=args.department,
            )
        elif args.type == "reminder":
            success = send_reminder_emails(
                days_before=args.days_before, dry_run=args.dry_run
            )

        if success:
            logger.info("Email sending completed successfully!")
        else:
            logger.error("Email sending completed with errors.")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nEmail sending interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
