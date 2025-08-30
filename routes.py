from flask import render_template, request, jsonify, redirect, url_for, flash, make_response
from datetime import datetime, timedelta
import uuid
import qrcode
import io
import base64
from app import app, db
from models import Participant, Dependent, CheckIn, DeliveryItem, DeliveryLog, EmailLog
from utils import generate_qr_code, send_qr_email

@app.route('/')
def index():
    """Homepage with overview"""
    total_participants = Participant.query.count()
    total_checkins = CheckIn.query.count()
    total_items = DeliveryItem.query.count()
    pending_checkins = total_participants - total_checkins
    
    return render_template('index.html', stats={
        'total_participants': total_participants,
        'total_checkins': total_checkins,
        'total_items': total_items,
        'pending_checkins': pending_checkins
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Participant registration with dependents"""
    if request.method == 'POST':
        try:
            # Create participant with unique QR code
            qr_code = str(uuid.uuid4())[:8].upper()
            
            participant = Participant(
                nome=request.form['nome'].strip(),
                email=request.form['email'].strip().lower(),
                telefone=request.form.get('telefone', '').strip(),
                departamento=request.form.get('departamento', '').strip(),
                qr_code=qr_code
            )
            db.session.add(participant)
            db.session.flush()  # Get participant ID
            
            # Add dependents (up to 5)
            dependent_count = 0
            for i in range(1, 6):
                dependent_name = request.form.get(f'dependent_{i}')
                if dependent_name and dependent_name.strip():
                    dependent = Dependent(
                        nome=dependent_name.strip(),
                        idade=int(request.form.get(f'dependent_age_{i}', 0) or 0),
                        participant_id=participant.id
                    )
                    db.session.add(dependent)
                    dependent_count += 1
            
            db.session.commit()
            flash(f'Inscrição realizada com sucesso! QR Code: {qr_code}', 'success')
            
            # Log the registration
            app.logger.info(f'New participant registered: {participant.nome} ({participant.email}) with {dependent_count} dependents')
            
            return redirect(url_for('success', participant_id=participant.id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Registration error: {str(e)}')
            flash('Erro ao realizar inscrição. Tente novamente.', 'error')
    
    return render_template('register.html')

@app.route('/success/<int:participant_id>')
def success(participant_id):
    """Registration success page with QR code"""
    participant = Participant.query.get_or_404(participant_id)
    
    # Generate QR code image
    qr_img = generate_qr_code(participant.qr_code)
    
    return render_template('success.html', participant=participant, qr_image=qr_img)

@app.route('/scanner')
def scanner():
    """QR code scanner interface"""
    return render_template('scanner.html')

@app.route('/checkin/search')
def checkin_search():
    """Manual participant search for offline check-in"""
    return render_template('checkin_search.html')

@app.route('/dashboard')
def dashboard():
    """Real-time check-in dashboard"""
    total_participants = Participant.query.count()
    total_checkins = CheckIn.query.count()
    pending_checkins = total_participants - total_checkins
    
    # Recent check-ins (last 10)
    recent_checkins = db.session.query(CheckIn, Participant)\
        .join(Participant)\
        .order_by(CheckIn.checkin_time.desc())\
        .limit(10).all()
    
    # Hourly check-in stats for chart
    today = datetime.now().date()
    hourly_stats = []
    for hour in range(24):
        hour_start = datetime.combine(today, datetime.min.time().replace(hour=hour))
        hour_end = hour_start + timedelta(hours=1)
        count = CheckIn.query.filter(
            CheckIn.checkin_time >= hour_start,
            CheckIn.checkin_time < hour_end
        ).count()
        hourly_stats.append({'hour': hour, 'count': count})
    
    return render_template('dashboard.html', 
                         stats={
                             'total_participants': total_participants,
                             'total_checkins': total_checkins,
                             'pending_checkins': pending_checkins
                         },
                         recent_checkins=recent_checkins,
                         hourly_stats=hourly_stats)

@app.route('/delivery')
def delivery():
    """Delivery management interface"""
    items_by_category = {}
    categories = ['Festa', 'Cesta Básica', 'Brinquedos', 'Material Escolar']
    
    for category in categories:
        items = DeliveryItem.query.filter_by(categoria=category).all()
        items_by_category[category] = items
    
    return render_template('delivery.html', items_by_category=items_by_category)

@app.route('/inventory')
def inventory():
    """Inventory management"""
    items = DeliveryItem.query.order_by(DeliveryItem.categoria, DeliveryItem.nome).all()
    return render_template('inventory.html', items=items)

# API Routes
@app.route('/api/validate_qr', methods=['POST'])
def validate_qr():
    """Validate QR code and perform check-in"""
    try:
        data = request.get_json()
        qr_code = data.get('qr_code', '').strip().upper()
        station = data.get('station', 'main')
        
        if not qr_code:
            return jsonify({'success': False, 'message': 'QR Code é obrigatório'})
        
        participant = Participant.query.filter_by(qr_code=qr_code).first()
        
        if not participant:
            return jsonify({'success': False, 'message': 'QR Code inválido'})
        
        # Check if already checked in
        existing_checkin = CheckIn.query.filter_by(participant_id=participant.id).first()
        if existing_checkin:
            return jsonify({
                'success': False, 
                'message': f'Participante já fez check-in às {existing_checkin.checkin_time.strftime("%H:%M")}',
                'already_checked_in': True,
                'checkin_time': existing_checkin.checkin_time.strftime("%H:%M")
            })
        
        # Create check-in
        checkin = CheckIn(
            participant_id=participant.id,
            station=station,
            operator=data.get('operator', 'Sistema')
        )
        db.session.add(checkin)
        db.session.commit()
        
        app.logger.info(f'Check-in successful: {participant.nome} ({qr_code}) at station {station}')
        
        return jsonify({
            'success': True,
            'message': 'Check-in realizado com sucesso!',
            'participant': {
                'nome': participant.nome,
                'email': participant.email,
                'departamento': participant.departamento,
                'dependents_count': len(participant.dependents),
                'qr_code': participant.qr_code,
                'checkin_time': checkin.checkin_time.strftime("%H:%M")
            }
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Check-in error: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro interno do sistema'})

@app.route('/api/search_participant')
def search_participant():
    """Search participants by name"""
    query = request.args.get('q', '').strip().lower()
    
    if len(query) < 2:
        return jsonify([])
    
    participants = Participant.query.filter(
        Participant.nome.ilike(f'%{query}%')
    ).limit(10).all()
    
    results = []
    for p in participants:
        checkin = CheckIn.query.filter_by(participant_id=p.id).first()
        results.append({
            'id': p.id,
            'nome': p.nome,
            'email': p.email,
            'departamento': p.departamento,
            'qr_code': p.qr_code,
            'dependents_count': len(p.dependents),
            'checked_in': bool(checkin),
            'checkin_time': checkin.checkin_time.strftime('%H:%M') if checkin else None
        })
    
    return jsonify(results)

@app.route('/api/manual_checkin', methods=['POST'])
def manual_checkin():
    """Manual check-in for offline mode"""
    try:
        data = request.get_json()
        participant_id = data.get('participant_id')
        station = data.get('station', 'manual')
        
        participant = Participant.query.get(participant_id)
        if not participant:
            return jsonify({'success': False, 'message': 'Participante não encontrado'})
        
        # Check if already checked in
        existing_checkin = CheckIn.query.filter_by(participant_id=participant.id).first()
        if existing_checkin:
            return jsonify({
                'success': False, 
                'message': f'Participante já fez check-in às {existing_checkin.checkin_time.strftime("%H:%M")}'
            })
        
        # Create check-in
        checkin = CheckIn(
            participant_id=participant.id,
            station=station,
            operator=data.get('operator', 'Manual')
        )
        db.session.add(checkin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Check-in manual realizado com sucesso!',
            'participant': {
                'nome': participant.nome,
                'checkin_time': checkin.checkin_time.strftime("%H:%M")
            }
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Manual check-in error: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro interno do sistema'})

@app.route('/api/dashboard_stats')
def dashboard_stats():
    """Real-time dashboard statistics"""
    total_participants = Participant.query.count()
    total_checkins = CheckIn.query.count()
    pending_checkins = total_participants - total_checkins
    
    # Recent check-ins
    recent = db.session.query(CheckIn, Participant)\
        .join(Participant)\
        .order_by(CheckIn.checkin_time.desc())\
        .limit(5).all()
    
    recent_checkins = [{
        'nome': p.nome,
        'departamento': p.departamento,
        'checkin_time': c.checkin_time.strftime('%H:%M'),
        'station': c.station
    } for c, p in recent]
    
    return jsonify({
        'total_participants': total_participants,
        'total_checkins': total_checkins,
        'pending_checkins': pending_checkins,
        'recent_checkins': recent_checkins
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected'
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Server error: {error}')
    return render_template('500.html'), 500
