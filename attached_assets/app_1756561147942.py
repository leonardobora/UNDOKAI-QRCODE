#!/usr/bin/env python3
"""
Lightera BUNDOKAI - Sistema de Check-in e Controle de Entregas
Substitui solução Digitevent (R$ 5.427,00) para eventos corporativos
Capacidade: até 2500 participantes
"""

import base64
import os
import uuid
from datetime import datetime, timedelta
from io import BytesIO

import pandas as pd
import qrcode
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "lightera-bundokai-secret-key-2024"
)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///bundokai.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Models
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(20))
    departamento = db.Column(db.String(50))
    qr_code = db.Column(db.String(50), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dependents = db.relationship("Dependent", backref="participant", lazy=True)
    checkins = db.relationship("CheckIn", backref="participant", lazy=True)


class Dependent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer)
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )


class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )
    checkin_time = db.Column(db.DateTime, default=datetime.utcnow)
    station = db.Column(db.String(20), default="main")
    status = db.Column(db.String(20), default="checked_in")


class DeliveryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    categoria = db.Column(
        db.String(50)
    )  # Festa, Cesta Básica, Brinquedos, Material Escolar
    estoque_inicial = db.Column(db.Integer, default=0)
    estoque_atual = db.Column(db.Integer, default=0)


class DeliveryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )
    item_id = db.Column(db.Integer, db.ForeignKey("delivery_item.id"), nullable=False)
    delivery_time = db.Column(db.DateTime, default=datetime.utcnow)
    quantidade = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default="delivered")


# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Create participant with QR code
        participant = Participant(
            nome=request.form["nome"],
            email=request.form["email"],
            telefone=request.form.get("telefone"),
            departamento=request.form.get("departamento"),
            qr_code=str(uuid.uuid4())[:8].upper(),
        )
        db.session.add(participant)

        # Add dependents
        for i in range(1, 6):  # Max 5 dependents
            dependent_name = request.form.get(f"dependent_{i}")
            if dependent_name:
                dependent = Dependent(
                    nome=dependent_name,
                    idade=request.form.get(f"dependent_age_{i}", 0),
                    participant=participant,
                )
                db.session.add(dependent)

        db.session.commit()
        flash("Inscrição realizada com sucesso!")
        return redirect(url_for("success", participant_id=participant.id))

    return render_template("register.html")


@app.route("/scanner")
def scanner():
    return render_template("scanner.html")


@app.route("/checkin/search")
def checkin_search():
    return render_template("checkin_search.html")


@app.route("/api/validate_qr", methods=["POST"])
def validate_qr():
    qr_code = request.json.get("qr_code")
    participant = Participant.query.filter_by(qr_code=qr_code).first()

    if not participant:
        return jsonify({"success": False, "message": "QR Code inválido"})

    # Check if already checked in
    existing_checkin = CheckIn.query.filter_by(participant_id=participant.id).first()
    if existing_checkin:
        return jsonify(
            {
                "success": False,
                "message": f'Participante já fez check-in às {existing_checkin.checkin_time.strftime("%H:%M")}',
            }
        )

    # Create check-in
    checkin = CheckIn(participant_id=participant.id)
    db.session.add(checkin)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "participant": {
                "nome": participant.nome,
                "email": participant.email,
                "departamento": participant.departamento,
                "dependents_count": len(participant.dependents),
            },
        }
    )


@app.route("/api/search_participant")
def search_participant():
    query = request.args.get("q", "").lower()
    participants = (
        Participant.query.filter(Participant.nome.contains(query)).limit(10).all()
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
                "dependents_count": len(p.dependents),
                "checked_in": bool(checkin),
                "checkin_time": (
                    checkin.checkin_time.strftime("%H:%M") if checkin else None
                ),
            }
        )

    return jsonify(results)


@app.route("/dashboard")
def dashboard():
    total_participants = Participant.query.count()
    total_checkins = CheckIn.query.count()
    pending_checkins = total_participants - total_checkins

    # Recent check-ins
    recent_checkins = (
        db.session.query(CheckIn, Participant)
        .join(Participant)
        .order_by(CheckIn.checkin_time.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "dashboard.html",
        stats={
            "total_participants": total_participants,
            "total_checkins": total_checkins,
            "pending_checkins": pending_checkins,
        },
        recent_checkins=recent_checkins,
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
