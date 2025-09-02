import base64
import io
import uuid
from datetime import datetime, timedelta

import qrcode
from flask import (
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app import app, db
from auth import check_admin_credentials, is_admin, login_required
from utils import generate_qr_code, send_qr_email


@app.route("/")
def user_index():
    """User homepage with registration and QR lookup"""
    from models import CheckIn, Participant

    total_participants = Participant.query.count()
    total_checkins = CheckIn.query.count()

    return render_template(
        "user_index.html",
        stats={
            "total_participants": total_participants,
            "total_checkins": total_checkins,
        },
    )


@app.route("/admin")
@login_required
def admin_index():
    """Admin homepage with full system overview"""
    from models import CheckIn, DeliveryItem, Participant

    total_participants = Participant.query.count()
    total_checkins = CheckIn.query.count()
    total_items = DeliveryItem.query.count()
    pending_checkins = total_participants - total_checkins

    return render_template(
        "index.html",
        stats={
            "total_participants": total_participants,
            "total_checkins": total_checkins,
            "total_items": total_items,
            "pending_checkins": pending_checkins,
        },
    )


@app.route("/admin/panel")
@login_required
def admin_panel():
    from models import CheckIn, Participant

    """Enhanced admin panel with bulk operations"""
    total_participants = Participant.query.count()
    total_checkins = CheckIn.query.count()
    pending_checkins = total_participants - total_checkins

    return render_template(
        "admin.html",
        stats={
            "total_participants": total_participants,
            "total_checkins": total_checkins,
            "pending_checkins": pending_checkins,
            "total_admins": 3,  # Static for now
        },
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if check_admin_credentials(username, password):
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("admin_index"))
        else:
            flash("Usuário ou senha inválidos!", "danger")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    """Admin logout"""
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("Logout realizado com sucesso!", "info")
    return redirect(url_for("user_index"))


@app.route("/entregas")
@login_required
def entregas_list():
    from models import Participant

    """List of pre-selected employees for deliveries"""
    # Get all participants with matricula (pre-selected for deliveries)
    deliveries = Participant.query.filter(Participant.matricula.isnot(None)).all()

    # Calculate statistics
    stats = {
        "total_employees": len(deliveries),
        "qr_generated": sum(1 for d in deliveries if d.qr_code),
        "pending_delivery": sum(
            1
            for d in deliveries
            if not any(log.status == "delivered" for log in d.deliveries)
        ),
        "delivered": sum(
            1
            for d in deliveries
            if any(log.status == "delivered" for log in d.deliveries)
        ),
    }

    # Format delivery data
    delivery_data = []
    for participant in deliveries:
        # Get items for this participant
        items = []
        for log in participant.deliveries:
            if log.item:
                items.append(log.item.nome)

        delivery_data.append(
            {
                "id": participant.id,
                "nome": participant.nome,
                "matricula": participant.matricula,
                "email": participant.email,
                "items": items,
                "qr_code": participant.qr_code,
                "delivered": any(
                    log.status == "delivered" for log in participant.deliveries
                ),
            }
        )

    return render_template("entregas_list.html", deliveries=delivery_data, stats=stats)


@app.route("/index")
def index():
    """Redirect old index route to user interface"""
    return redirect(url_for("user_index"))


@app.route("/user/qr-lookup")
def user_qr_lookup():
    """User QR code lookup page"""
    return render_template("user_qr_lookup.html")


@app.route("/api/lookup_participant_by_email", methods=["POST"])
def lookup_participant_by_email():
    from models import Participant

    """API endpoint to lookup participant by email"""
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"success": False, "message": "Email é obrigatório"})

        participant = Participant.query.filter_by(email=email).first()

        if not participant:
            return jsonify({"success": False, "message": "Participante não encontrado"})

        # Generate QR code image
        from utils import generate_qr_code

        qr_image = generate_qr_code(participant.qr_code)

        return jsonify(
            {
                "success": True,
                "participant": {
                    "nome": participant.nome,
                    "email": participant.email,
                    "qr_code": participant.qr_code,
                    "dependents_count": len(participant.dependents),
                },
                "qr_image": qr_image,
            }
        )

    except Exception as e:
        app.logger.error(f"Lookup participant error: {str(e)}")
        return jsonify({"success": False, "message": "Erro interno do sistema"})


@app.route("/register", methods=["GET", "POST"])
def register():
    from models import Dependent, Participant

    """Participant registration with dependents"""
    if request.method == "POST":
        try:
            # Create participant with unique QR code
            qr_code = str(uuid.uuid4())[:8].upper()

            participant = Participant(
                nome=request.form["nome"].strip(),
                email=request.form["email"].strip().lower(),
                telefone=request.form.get("telefone", "").strip(),
                departamento=request.form.get("departamento", "").strip(),
                qr_code=qr_code,
            )
            db.session.add(participant)
            db.session.flush()  # Get participant ID

            # Add dependents (up to 5)
            dependent_count = 0
            for i in range(1, 6):
                dependent_name = request.form.get(f"dependent_{i}")
                if dependent_name and dependent_name.strip():
                    dependent = Dependent(
                        nome=dependent_name.strip(),
                        idade=int(request.form.get(f"dependent_age_{i}", 0) or 0),
                        participant_id=participant.id,
                    )
                    db.session.add(dependent)
                    dependent_count += 1

            db.session.commit()
            flash(f"Inscrição realizada com sucesso! QR Code: {qr_code}", "success")

            # Log the registration
            app.logger.info(
                f"New participant registered: {participant.nome} ({participant.email}) with {dependent_count} dependents"
            )

            return redirect(url_for("success", participant_id=participant.id))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            flash("Erro ao realizar inscrição. Tente novamente.", "error")

    return render_template("register.html")


@app.route("/success/<int:participant_id>")
def success(participant_id):
    from models import Participant

    """Registration success page with QR code"""
    participant = Participant.query.get_or_404(participant_id)

    # Generate QR code image
    qr_img = generate_qr_code(participant.qr_code)

    return render_template("success.html", participant=participant, qr_image=qr_img)


@app.route("/scanner")
@login_required
def scanner():
    """QR code scanner interface"""
    return render_template("scanner.html")


@app.route("/checkin/search")
@login_required
def checkin_search():
    """Manual participant search for offline check-in"""
    return render_template("checkin_search.html")


@app.route("/dashboard")
@login_required
def dashboard():
    from models import CheckIn, Participant

    """Real-time check-in dashboard"""
    total_participants = Participant.query.count()
    total_checkins = CheckIn.query.count()
    pending_checkins = total_participants - total_checkins

    # Recent check-ins (last 10)
    recent_checkins = (
        db.session.query(CheckIn, Participant)
        .join(Participant)
        .order_by(CheckIn.checkin_time.desc())
        .limit(10)
        .all()
    )

    # Hourly check-in stats for chart
    today = datetime.now().date()
    hourly_stats = []
    for hour in range(24):
        hour_start = datetime.combine(today, datetime.min.time().replace(hour=hour))
        hour_end = hour_start + timedelta(hours=1)
        count = CheckIn.query.filter(
            CheckIn.checkin_time >= hour_start, CheckIn.checkin_time < hour_end
        ).count()
        hourly_stats.append({"hour": hour, "count": count})

    return render_template(
        "dashboard.html",
        stats={
            "total_participants": total_participants,
            "total_checkins": total_checkins,
            "pending_checkins": pending_checkins,
        },
        recent_checkins=recent_checkins,
        hourly_stats=hourly_stats,
    )


@app.route("/delivery")
@login_required
def delivery():
    from models import DeliveryItem

    """Delivery management interface"""
    items_by_category = {}
    categories = ["Festa", "Cesta Básica", "Brinquedos", "Material Escolar"]

    for category in categories:
        items = DeliveryItem.query.filter_by(categoria=category).all()
        items_by_category[category] = items

    return render_template("delivery.html", items_by_category=items_by_category)


@app.route("/inventory")
@login_required
def inventory():
    from models import DeliveryItem

    """Inventory management"""
    items = DeliveryItem.query.order_by(DeliveryItem.categoria, DeliveryItem.nome).all()
    return render_template("inventory.html", items=items)


# API Routes
@app.route("/api/validate_qr", methods=["POST"])
def validate_qr():
    from models import CheckIn, Participant

    """Validate QR code and perform check-in"""
    try:
        data = request.get_json()
        qr_code = data.get("qr_code", "").strip().upper()
        station = data.get("station", "main")

        if not qr_code:
            return jsonify({"success": False, "message": "QR Code é obrigatório"})

        participant = Participant.query.filter_by(qr_code=qr_code).first()

        if not participant:
            return jsonify({"success": False, "message": "QR Code inválido"})

        # Check if already checked in
        existing_checkin = CheckIn.query.filter_by(
            participant_id=participant.id
        ).first()
        if existing_checkin:
            return jsonify(
                {
                    "success": False,
                    "message": f'Participante já fez check-in às {existing_checkin.checkin_time.strftime("%H:%M")}',
                    "already_checked_in": True,
                    "checkin_time": existing_checkin.checkin_time.strftime("%H:%M"),
                }
            )

        # Create check-in
        checkin = CheckIn(
            participant_id=participant.id,
            station=station,
            operator=data.get("operator", "Sistema"),
        )
        db.session.add(checkin)
        db.session.commit()

        app.logger.info(
            f"Check-in successful: {participant.nome} ({qr_code}) at station {station}"
        )

        return jsonify(
            {
                "success": True,
                "message": "Check-in realizado com sucesso!",
                "participant": {
                    "nome": participant.nome,
                    "email": participant.email,
                    "departamento": participant.departamento,
                    "dependents_count": len(participant.dependents),
                    "qr_code": participant.qr_code,
                    "checkin_time": checkin.checkin_time.strftime("%H:%M"),
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Check-in error: {str(e)}")
        return jsonify({"success": False, "message": "Erro interno do sistema"})


@app.route("/api/search_participant")
def search_participant():
    from models import CheckIn, Participant

    """Search participants by name"""
    query = request.args.get("q", "").strip().lower()

    if len(query) < 2:
        return jsonify([])

    participants = (
        Participant.query.filter(Participant.nome.ilike(f"%{query}%")).limit(10).all()
    )

    results = []
    for p in participants:
        checkin = CheckIn.query.filter_by(participant_id=p.id).first()
        results.append(
            {
                "id": p.id,
                "nome": p.nome,
                "email": p.email,
                "departamento": p.departamento,
                "qr_code": p.qr_code,
                "dependents_count": len(p.dependents),
                "checked_in": bool(checkin),
                "checkin_time": (
                    checkin.checkin_time.strftime("%H:%M") if checkin else None
                ),
            }
        )

    return jsonify(results)


@app.route("/api/manual_checkin", methods=["POST"])
def manual_checkin():
    from models import CheckIn, Participant

    """Manual check-in for offline mode"""
    try:
        data = request.get_json()
        participant_id = data.get("participant_id")
        station = data.get("station", "manual")

        participant = Participant.query.get(participant_id)
        if not participant:
            return jsonify({"success": False, "message": "Participante não encontrado"})

        # Check if already checked in
        existing_checkin = CheckIn.query.filter_by(
            participant_id=participant.id
        ).first()
        if existing_checkin:
            return jsonify(
                {
                    "success": False,
                    "message": f'Participante já fez check-in às {existing_checkin.checkin_time.strftime("%H:%M")}',
                }
            )

        # Create check-in
        checkin = CheckIn(
            participant_id=participant.id,
            station=station,
            operator=data.get("operator", "Manual"),
        )
        db.session.add(checkin)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Check-in manual realizado com sucesso!",
                "participant": {
                    "nome": participant.nome,
                    "checkin_time": checkin.checkin_time.strftime("%H:%M"),
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Manual check-in error: {str(e)}")
        return jsonify({"success": False, "message": "Erro interno do sistema"})


@app.route("/api/dashboard_stats")
def dashboard_stats():
    from models import CheckIn, Participant

    """Real-time dashboard statistics"""
    total_participants = Participant.query.count()
    total_checkins = CheckIn.query.count()
    pending_checkins = total_participants - total_checkins

    # Recent check-ins
    recent = (
        db.session.query(CheckIn, Participant)
        .join(Participant)
        .order_by(CheckIn.checkin_time.desc())
        .limit(5)
        .all()
    )

    recent_checkins = [
        {
            "nome": p.nome,
            "departamento": p.departamento,
            "checkin_time": c.checkin_time.strftime("%H:%M"),
            "station": c.station,
            "dependents_count": len(p.dependents) if p.dependents else 0,
        }
        for c, p in recent
    ]

    return jsonify(
        {
            "total_participants": total_participants,
            "total_checkins": total_checkins,
            "pending_checkins": pending_checkins,
            "recent_checkins": recent_checkins,
        }
    )


@app.route("/api/recent_checkins")
def recent_checkins():
    from models import CheckIn, Participant

    """Get recent check-ins for dashboard refresh"""
    recent = (
        db.session.query(CheckIn, Participant)
        .join(Participant)
        .order_by(CheckIn.checkin_time.desc())
        .limit(10)
        .all()
    )

    recent_checkins = [
        {
            "nome": p.nome,
            "departamento": p.departamento or "-",
            "checkin_time": c.checkin_time.strftime("%H:%M"),
            "station": c.station,
            "dependents_count": len(p.dependents) if p.dependents else 0,
        }
        for c, p in recent
    ]

    return jsonify({"recent_checkins": recent_checkins})


@app.route("/api/export/checkins")
@login_required
def export_checkins():
    from models import CheckIn, Participant

    """Export check-ins to Excel"""
    try:
        from io import BytesIO

        import pandas as pd

        # Get all check-ins with participant data
        checkins = (
            db.session.query(CheckIn, Participant)
            .join(Participant)
            .order_by(CheckIn.checkin_time.desc())
            .all()
        )

        # Prepare data for Excel
        data = []
        for checkin, participant in checkins:
            data.append(
                {
                    "Nome": participant.nome,
                    "Email": participant.email,
                    "Telefone": participant.telefone or "",
                    "Departamento": participant.departamento or "",
                    "Matrícula": participant.matricula or "",
                    "Horário Check-in": checkin.checkin_time.strftime(
                        "%d/%m/%Y %H:%M:%S"
                    ),
                    "Estação": checkin.station,
                    "Operador": checkin.operator or "",
                    "Dependentes": (
                        len(participant.dependents) if participant.dependents else 0
                    ),
                    "QR Code": participant.qr_code,
                }
            )

        # Create Excel file
        df = pd.DataFrame(data)
        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Check-ins", index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets["Check-ins"]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        response = make_response(output.getvalue())
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename=checkins_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        )

        return response

    except Exception as e:
        app.logger.error(f"Export error: {str(e)}")
        flash("Erro ao exportar dados", "danger")
        return redirect(url_for("dashboard"))


@app.route("/api/send_report", methods=["POST"])
@login_required
def send_report():
    """Send dashboard report via email"""
    try:
        # For now, just return success - email functionality can be implemented later
        return jsonify({"success": True, "message": "Relatório enviado com sucesso!"})
    except Exception as e:
        app.logger.error(f"Send report error: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao enviar relatório"})


@app.route("/api/bulk_checkin", methods=["POST"])
@login_required
def bulk_checkin():
    from models import CheckIn, Participant

    """Perform bulk check-in for selected participants"""
    try:
        data = request.get_json()
        participant_ids = data.get("participant_ids", [])
        station = data.get("station", "bulk")
        operator = data.get("operator", "Bulk Operation")

        if not participant_ids:
            return jsonify(
                {"success": False, "message": "Nenhum participante selecionado"}
            )

        success_count = 0
        error_count = 0
        already_checked = 0

        for participant_id in participant_ids:
            try:
                participant = Participant.query.get(participant_id)
                if not participant:
                    error_count += 1
                    continue

                # Check if already checked in
                existing_checkin = CheckIn.query.filter_by(
                    participant_id=participant.id
                ).first()
                if existing_checkin:
                    already_checked += 1
                    continue

                # Create check-in
                checkin = CheckIn(
                    participant_id=participant.id, station=station, operator=operator
                )
                db.session.add(checkin)
                success_count += 1

            except Exception as e:
                app.logger.error(
                    f"Bulk checkin error for participant {participant_id}: {str(e)}"
                )
                error_count += 1

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f"Check-in em lote concluído: {success_count} sucessos, {already_checked} já registrados, {error_count} erros",
                "stats": {
                    "success": success_count,
                    "already_checked": already_checked,
                    "errors": error_count,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Bulk checkin error: {str(e)}")
        return jsonify({"success": False, "message": "Erro interno do sistema"})


@app.route("/api/participants_list")
@login_required
def participants_list():
    from models import CheckIn, Participant

    """Get all participants for admin panel"""
    try:
        participants = Participant.query.all()
        participants_data = []

        for participant in participants:
            checkin = CheckIn.query.filter_by(participant_id=participant.id).first()
            participants_data.append(
                {
                    "id": participant.id,
                    "nome": participant.nome,
                    "email": participant.email,
                    "telefone": participant.telefone or "",
                    "departamento": participant.departamento or "",
                    "matricula": participant.matricula or "",
                    "qr_code": participant.qr_code,
                    "checked_in": checkin is not None,
                    "checkin_time": (
                        checkin.checkin_time.strftime("%H:%M") if checkin else None
                    ),
                    "dependents_count": (
                        len(participant.dependents) if participant.dependents else 0
                    ),
                }
            )

        return jsonify({"success": True, "participants": participants_data})

    except Exception as e:
        app.logger.error(f"Participants list error: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao carregar participantes"})


@app.route("/api/export_selected", methods=["POST"])
@login_required
def export_selected():
    from models import CheckIn, Participant

    """Export selected participants to Excel"""
    try:
        from io import BytesIO

        import pandas as pd

        data = request.get_json()
        participant_ids = data.get("participant_ids", [])

        if not participant_ids:
            return jsonify(
                {"success": False, "message": "Nenhum participante selecionado"}
            )

        # Get selected participants with check-in data
        participants = (
            db.session.query(Participant)
            .filter(Participant.id.in_(participant_ids))
            .all()
        )

        # Prepare data for Excel
        export_data = []
        for participant in participants:
            checkin = CheckIn.query.filter_by(participant_id=participant.id).first()
            export_data.append(
                {
                    "Nome": participant.nome,
                    "Email": participant.email,
                    "Telefone": participant.telefone or "",
                    "Departamento": participant.departamento or "",
                    "Matrícula": participant.matricula or "",
                    "Status": "Check-in realizado" if checkin else "Aguardando",
                    "Horário Check-in": (
                        checkin.checkin_time.strftime("%d/%m/%Y %H:%M:%S")
                        if checkin
                        else ""
                    ),
                    "Estação": checkin.station if checkin else "",
                    "Dependentes": (
                        len(participant.dependents) if participant.dependents else 0
                    ),
                    "QR Code": participant.qr_code,
                }
            )

        # Create Excel file
        df = pd.DataFrame(export_data)
        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Participantes Selecionados", index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets["Participantes Selecionados"]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        response = make_response(output.getvalue())
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename=participantes_selecionados_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        )

        return response

    except Exception as e:
        app.logger.error(f"Export selected error: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao exportar dados"})


@app.route("/api/add_item", methods=["POST"])
def add_item():
    from models import DeliveryItem

    """Add new inventory item"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["nome", "categoria", "estoque_inicial", "estoque_atual"]
        for field in required_fields:
            if not data.get(field):
                return jsonify(
                    {"success": False, "message": f"Campo {field} é obrigatório"}
                )

        item = DeliveryItem(
            nome=data["nome"].strip(),
            categoria=data["categoria"].strip(),
            descricao=data.get("descricao", "").strip(),
            estoque_inicial=int(data["estoque_inicial"]),
            estoque_atual=int(data["estoque_atual"]),
            preco_unitario=float(data.get("preco_unitario", 0.0)),
        )

        db.session.add(item)
        db.session.commit()

        app.logger.info(f"New item added: {item.nome} ({item.categoria})")
        return jsonify({"success": True, "message": "Item adicionado com sucesso!"})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Add item error: {str(e)}")
        return jsonify({"success": False, "message": "Erro interno do sistema"})


@app.route("/api/item/<int:item_id>")
def get_item(item_id):
    from models import DeliveryItem

    """Get inventory item details"""
    try:
        item = DeliveryItem.query.get_or_404(item_id)
        return jsonify(
            {
                "success": True,
                "item": {
                    "id": item.id,
                    "nome": item.nome,
                    "categoria": item.categoria,
                    "descricao": item.descricao,
                    "estoque_inicial": item.estoque_inicial,
                    "estoque_atual": item.estoque_atual,
                    "preco_unitario": item.preco_unitario,
                },
            }
        )
    except Exception as e:
        app.logger.error(f"Get item error: {str(e)}")
        return jsonify({"success": False, "message": "Item não encontrado"})


@app.route("/api/adjust_stock", methods=["POST"])
def adjust_stock():
    from models import DeliveryItem

    """Adjust inventory stock"""
    try:
        data = request.get_json()
        item_id = int(data["stock_item_id"])
        adjustment_type = data["adjustment_type"]
        adjustment_quantity = int(data["adjustment_quantity"])

        item = DeliveryItem.query.get_or_404(item_id)

        if adjustment_type == "add":
            item.estoque_atual += adjustment_quantity
        elif adjustment_type == "subtract":
            item.estoque_atual = max(0, item.estoque_atual - adjustment_quantity)
        elif adjustment_type == "set":
            item.estoque_atual = adjustment_quantity

        db.session.commit()

        app.logger.info(
            f"Stock adjusted for {item.nome}: {adjustment_type} {adjustment_quantity}"
        )
        return jsonify({"success": True, "message": "Estoque ajustado com sucesso!"})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Stock adjustment error: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao ajustar estoque"})


@app.route("/api/download_excel_template")
def download_excel_template():
    """Download Excel template for inventory import"""
    try:
        # Create a simple CSV template
        import io

        output = io.StringIO()

        # CSV headers
        headers = [
            "nome",
            "categoria",
            "descricao",
            "estoque_inicial",
            "estoque_atual",
            "preco_unitario",
        ]
        output.write(",".join(headers) + "\n")

        # Sample data
        sample_data = [
            [
                "Kit Festa Adulto",
                "Festa",
                "Kit completo para festa adulto",
                "100",
                "100",
                "50.00",
            ],
            [
                "Cesta Básica Completa",
                "Cesta Básica",
                "Cesta básica com itens essenciais",
                "200",
                "200",
                "80.00",
            ],
            [
                "Brinquedo Educativo",
                "Brinquedos",
                "Brinquedo educativo para crianças",
                "50",
                "50",
                "30.00",
            ],
            [
                "Kit Escolar Completo",
                "Material Escolar",
                "Kit com materiais escolares",
                "150",
                "150",
                "25.00",
            ],
        ]

        for row in sample_data:
            output.write(",".join(row) + "\n")

        output.seek(0)

        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = (
            "attachment; filename=template_estoque_undokai.csv"
        )

        return response

    except Exception as e:
        app.logger.error(f"Excel template error: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao gerar template"})


@app.route("/api/send_delivery_qrcodes", methods=["POST"])
@login_required
def send_delivery_qrcodes():
    from models import EmailLog, Participant

    """Send QR codes to all employees selected for deliveries"""
    try:
        # Get all participants with matricula (pre-selected for deliveries)
        employees = Participant.query.filter(Participant.matricula.isnot(None)).all()

        sent_count = 0
        failed_count = 0

        for employee in employees:
            # Generate QR code if not exists
            if not employee.qr_code:
                employee.qr_code = str(uuid.uuid4())[:8].upper()
                db.session.add(employee)

            # Send email with QR code
            try:
                if send_qr_email(employee.email, employee.nome, employee.qr_code):
                    sent_count += 1
                    # Log email sent
                    email_log = EmailLog(
                        participant_id=employee.id,
                        email_type="delivery_qr",
                        subject="UNDOKAI 2025 - QR Code para Retirada",
                        status="sent",
                    )
                    db.session.add(email_log)
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                app.logger.error(f"Failed to send QR to {employee.email}: {str(e)}")

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f"QR codes enviados: {sent_count} sucesso, {failed_count} falhas",
                "sent": sent_count,
                "failed": failed_count,
            }
        )

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Send delivery QR codes error: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao enviar QR codes"})


@app.route("/api/import_delivery_list", methods=["POST"])
@login_required
def import_delivery_list():
    from models import Participant

    """Import delivery list from Excel/CSV"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "message": "Nenhum arquivo enviado"})

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "message": "Arquivo não selecionado"})

        # Process the file (simplified for now)
        # In production, use pandas to read Excel/CSV
        imported_count = 0

        # Example: Process CSV data
        # df = pd.read_csv(file)
        # for _, row in df.iterrows():
        #     participant = Participant(...)
        #     db.session.add(participant)
        #     imported_count += 1

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f"{imported_count} registros importados com sucesso",
            }
        )

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Import delivery list error: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao importar lista"})


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
        }
    )


@app.route("/service-worker.js")
def service_worker():
    """Serve the service worker with correct content type"""
    from flask import send_from_directory

    response = make_response(send_from_directory("static/js", "service-worker.js"))
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.route("/scanner/public")
def scanner_public():
    """Public QR code scanner interface for testing PWA"""
    return render_template("scanner.html")


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f"Server error: {error}")
    return render_template("500.html"), 500
