import qrcode
import io
import base64
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from app import app, db

def generate_qr_code(data, size=10, border=4):
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def send_qr_email(participant, qr_image_data=None):
    """Send QR code via email"""
    try:
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not all([smtp_username, smtp_password]):
            app.logger.warning('Email credentials not configured')
            return False
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = participant.email
        msg['Subject'] = f'BUNDOKAI 2024 - Seu QR Code de Acesso'
        
        # Email body
        body = f"""
        Olá {participant.nome},
        
        Sua inscrição para o BUNDOKAI 2024 foi confirmada!
        
        QR Code de Acesso: {participant.qr_code}
        
        Dependentes: {len(participant.dependents)}
        
        Apresente este QR Code na entrada do evento para realizar seu check-in.
        
        Atenciosamente,
        Equipe Lightera
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach QR code image if provided
        if qr_image_data:
            # Convert base64 to bytes
            img_data = base64.b64decode(qr_image_data.split(',')[1])
            img = MIMEImage(img_data)
            img.add_header('Content-Disposition', f'attachment; filename=qr_code_{participant.qr_code}.png')
            msg.attach(img)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        app.logger.info(f'QR code email sent to {participant.email}')
        return True
        
    except Exception as e:
        app.logger.error(f'Failed to send email to {participant.email}: {str(e)}')
        return False

def create_sample_delivery_items():
    """Create sample delivery items for testing"""
    from models import DeliveryItem
    from app import db
    
    sample_items = [
        # Festa category
        {'nome': 'Kit Festa Adulto', 'categoria': 'Festa', 'estoque_inicial': 500, 'estoque_atual': 500},
        {'nome': 'Kit Festa Infantil', 'categoria': 'Festa', 'estoque_inicial': 300, 'estoque_atual': 300},
        {'nome': 'Decoração Mesa', 'categoria': 'Festa', 'estoque_inicial': 100, 'estoque_atual': 100},
        
        # Cesta Básica category
        {'nome': 'Cesta Básica Completa', 'categoria': 'Cesta Básica', 'estoque_inicial': 800, 'estoque_atual': 800},
        {'nome': 'Cesta Básica Premium', 'categoria': 'Cesta Básica', 'estoque_inicial': 200, 'estoque_atual': 200},
        
        # Brinquedos category
        {'nome': 'Brinquedo 0-3 anos', 'categoria': 'Brinquedos', 'estoque_inicial': 150, 'estoque_atual': 150},
        {'nome': 'Brinquedo 4-7 anos', 'categoria': 'Brinquedos', 'estoque_inicial': 200, 'estoque_atual': 200},
        {'nome': 'Brinquedo 8-12 anos', 'categoria': 'Brinquedos', 'estoque_inicial': 180, 'estoque_atual': 180},
        
        # Material Escolar category
        {'nome': 'Kit Escolar Fundamental', 'categoria': 'Material Escolar', 'estoque_inicial': 300, 'estoque_atual': 300},
        {'nome': 'Kit Escolar Médio', 'categoria': 'Material Escolar', 'estoque_inicial': 200, 'estoque_atual': 200},
        {'nome': 'Mochila Escolar', 'categoria': 'Material Escolar', 'estoque_inicial': 250, 'estoque_atual': 250},
    ]
    
    for item_data in sample_items:
        existing = DeliveryItem.query.filter_by(nome=item_data['nome']).first()
        if not existing:
            item = DeliveryItem(**item_data)
            db.session.add(item)
    
    try:
        db.session.commit()
        app.logger.info('Sample delivery items created')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Failed to create sample items: {str(e)}')

def get_checkin_statistics():
    """Get comprehensive check-in statistics"""
    from models import Participant, CheckIn, Dependent
    
    total_participants = Participant.query.count()
    total_checkins = CheckIn.query.count()
    total_dependents = Dependent.query.count()
    
    # Department breakdown
    dept_stats = db.session.query(
        Participant.departamento,
        db.func.count(Participant.id).label('count')
    ).group_by(Participant.departamento).all()
    
    # Hourly breakdown for today
    today = datetime.now().date()
    hourly_checkins = []
    
    for hour in range(24):
        hour_start = datetime.combine(today, datetime.min.time().replace(hour=hour))
        hour_end = hour_start + timedelta(hours=1)
        count = CheckIn.query.filter(
            CheckIn.checkin_time >= hour_start,
            CheckIn.checkin_time < hour_end
        ).count()
        hourly_checkins.append({'hour': hour, 'count': count})
    
    return {
        'total_participants': total_participants,
        'total_checkins': total_checkins,
        'total_dependents': total_dependents,
        'pending_checkins': total_participants - total_checkins,
        'department_stats': dict(dept_stats),
        'hourly_checkins': hourly_checkins
    }
