from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class Participant(db.Model):
    """Model for event participants"""

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(20))
    departamento = db.Column(db.String(50))
    matricula = db.Column(db.String(50))  # Employee registration number
    qr_code = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    dependents = db.relationship(
        "Dependent", backref="participant", lazy=True, cascade="all, delete-orphan"
    )
    checkins = db.relationship("CheckIn", backref="participant", lazy=True)
    deliveries = db.relationship("DeliveryLog", backref="participant", lazy=True)

    def __repr__(self):
        return f"<Participant {self.nome}>"


class Dependent(db.Model):
    """Model for participant dependents"""

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer)
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )

    def __repr__(self):
        return f"<Dependent {self.nome}>"


class CheckIn(db.Model):
    """Model for event check-ins"""

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )
    checkin_time = db.Column(db.DateTime, default=datetime.utcnow)
    station = db.Column(db.String(20), default="main")
    status = db.Column(db.String(20), default="checked_in")
    operator = db.Column(db.String(50))

    def __repr__(self):
        return f"<CheckIn {self.participant.nome} at {self.checkin_time}>"


class DeliveryItem(db.Model):
    """Model for delivery inventory items"""

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    categoria = db.Column(
        db.String(50), nullable=False
    )  # Festa, Cesta Básica, Brinquedos, Material Escolar
    descricao = db.Column(db.Text)
    estoque_inicial = db.Column(db.Integer, default=0)
    estoque_atual = db.Column(db.Integer, default=0)
    preco_unitario = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    delivery_logs = db.relationship("DeliveryLog", backref="item", lazy=True)

    @property
    def items_delivered(self):
        return sum(
            log.quantidade for log in self.delivery_logs if log.status == "delivered"
        )

    @property
    def items_remaining(self):
        return self.estoque_atual

    def __repr__(self):
        return f"<DeliveryItem {self.nome}>"


class DeliveryLog(db.Model):
    """Model for delivery tracking"""

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )
    item_id = db.Column(db.Integer, db.ForeignKey("delivery_item.id"), nullable=False)
    matricula = db.Column(db.String(50))  # Employee registration for delivery
    delivery_time = db.Column(db.DateTime, default=datetime.utcnow)
    quantidade = db.Column(db.Integer, default=1)
    status = db.Column(
        db.String(20), default="delivered"
    )  # delivered, pending, cancelled
    operator = db.Column(db.String(50))
    notes = db.Column(db.Text)

    def __repr__(self):
        return f"<DeliveryLog {self.participant.nome} - {self.item.nome}>"


class EmailLog(db.Model):
    """Model for email tracking"""

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )
    email_type = db.Column(
        db.String(50), nullable=False
    )  # qr_delivery, reminder, confirmation
    subject = db.Column(db.String(200))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="sent")  # sent, failed, bounced
    opened_at = db.Column(db.DateTime)

    # Relationship
    participant_email = db.relationship("Participant", backref="emails")

    def __repr__(self):
        return f"<EmailLog {self.email_type} to {self.participant_email.email}>"
