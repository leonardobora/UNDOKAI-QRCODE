"""
Unit tests for database models.
"""

from datetime import datetime

import pytest

from app import db
from models import CheckIn, DeliveryItem, DeliveryLog, Dependent, EmailLog, Participant


class TestParticipant:
    """Test cases for Participant model."""

    def test_participant_creation(self, test_app, sample_participant):
        """Test creating a new participant."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.commit()

            # Verify participant was created
            participant = Participant.query.filter_by(
                email="joao.silva@lightera.com"
            ).first()
            assert participant is not None
            assert participant.nome == "João Silva"
            assert participant.email == "joao.silva@lightera.com"
            assert participant.telefone == "11999887766"
            assert participant.departamento == "TI"
            assert participant.matricula == "12345"
            assert participant.qr_code == "QR123456"
            assert participant.created_at is not None

    def test_participant_qr_code_unique(self, test_app):
        """Test that QR codes must be unique."""
        with test_app.app_context():
            # Create first participant
            participant1 = Participant(
                nome="João Silva", email="joao.silva@lightera.com", qr_code="QR123456"
            )
            db.session.add(participant1)
            db.session.commit()

            # Try to create second participant with same QR code
            participant2 = Participant(
                nome="Maria Santos",
                email="maria.santos@lightera.com",
                qr_code="QR123456",  # Same QR code
            )
            db.session.add(participant2)

            # This should raise an integrity error
            with pytest.raises(Exception):
                db.session.commit()

    def test_participant_repr(self, test_app, sample_participant):
        """Test participant string representation."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.commit()
            assert str(sample_participant) == "<Participant João Silva>"


class TestDependent:
    """Test cases for Dependent model."""

    def test_dependent_creation(self, test_app, sample_participant, sample_dependent):
        """Test creating a new dependent."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.flush()  # Get participant ID

            sample_dependent.participant_id = sample_participant.id
            db.session.add(sample_dependent)
            db.session.commit()

            # Verify dependent was created
            dependent = Dependent.query.filter_by(nome="Maria Silva").first()
            assert dependent is not None
            assert dependent.nome == "Maria Silva"
            assert dependent.idade == 8
            assert dependent.participant_id == sample_participant.id

    def test_dependent_relationship(
        self, test_app, sample_participant, sample_dependent
    ):
        """Test dependent-participant relationship."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.flush()

            sample_dependent.participant_id = sample_participant.id
            db.session.add(sample_dependent)
            db.session.commit()

            # Test relationship from participant side
            participant = Participant.query.first()
            assert len(participant.dependents) == 1
            assert participant.dependents[0].nome == "Maria Silva"

            # Test relationship from dependent side
            dependent = Dependent.query.first()
            assert dependent.participant.nome == "João Silva"

    def test_dependent_repr(self, sample_dependent):
        """Test dependent string representation."""
        assert str(sample_dependent) == "<Dependent Maria Silva>"


class TestCheckIn:
    """Test cases for CheckIn model."""

    def test_checkin_creation(self, test_app, sample_participant):
        """Test creating a new check-in."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.flush()

            checkin = CheckIn(
                participant_id=sample_participant.id,
                station="entrance",
                operator="admin_user",
            )
            db.session.add(checkin)
            db.session.commit()

            # Verify check-in was created
            saved_checkin = CheckIn.query.first()
            assert saved_checkin is not None
            assert saved_checkin.participant_id == sample_participant.id
            assert saved_checkin.station == "entrance"
            assert saved_checkin.operator == "admin_user"
            assert saved_checkin.status == "checked_in"  # Default value
            assert saved_checkin.checkin_time is not None

    def test_checkin_default_values(self, test_app, sample_participant):
        """Test check-in default values."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.flush()

            checkin = CheckIn(participant_id=sample_participant.id)
            db.session.add(checkin)
            db.session.commit()

            saved_checkin = CheckIn.query.first()
            assert saved_checkin.station == "main"  # Default value
            assert saved_checkin.status == "checked_in"  # Default value

    def test_checkin_relationship(self, test_app, sample_participant):
        """Test check-in participant relationship."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.flush()

            checkin = CheckIn(participant_id=sample_participant.id)
            db.session.add(checkin)
            db.session.commit()

            # Test relationship
            saved_checkin = CheckIn.query.first()
            assert saved_checkin.participant.nome == "João Silva"

            participant = Participant.query.first()
            assert len(participant.checkins) == 1
            assert participant.checkins[0].status == "checked_in"


class TestDeliveryItem:
    """Test cases for DeliveryItem model."""

    def test_delivery_item_creation(self, test_app, sample_delivery_item):
        """Test creating a new delivery item."""
        with test_app.app_context():
            db.session.add(sample_delivery_item)
            db.session.commit()

            # Verify delivery item was created
            item = DeliveryItem.query.filter_by(nome="Cesta Básica").first()
            assert item is not None
            assert item.nome == "Cesta Básica"
            assert item.categoria == "Cesta Básica"
            assert item.descricao == "Cesta com produtos básicos para final de ano"
            assert item.estoque_inicial == 100
            assert item.estoque_atual == 100
            assert item.preco_unitario == 50.0
            assert item.created_at is not None

    def test_delivery_item_properties(self, test_app, sample_delivery_item):
        """Test delivery item calculated properties."""
        with test_app.app_context():
            db.session.add(sample_delivery_item)
            db.session.flush()

            # Initially no deliveries
            assert sample_delivery_item.items_delivered == 0
            assert sample_delivery_item.items_remaining == 100

            # Add a delivery log (simulating a delivery)
            # Note: This would normally happen through the delivery process
            # but we're testing the property calculation
            assert (
                sample_delivery_item.items_remaining
                == sample_delivery_item.estoque_atual
            )

    def test_delivery_item_repr(self, sample_delivery_item):
        """Test delivery item string representation."""
        assert str(sample_delivery_item) == "<DeliveryItem Cesta Básica>"


class TestDeliveryLog:
    """Test cases for DeliveryLog model."""

    def test_delivery_log_creation(
        self, test_app, sample_participant, sample_delivery_item
    ):
        """Test creating a new delivery log."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.add(sample_delivery_item)
            db.session.flush()

            delivery_log = DeliveryLog(
                participant_id=sample_participant.id,
                item_id=sample_delivery_item.id,
                matricula="12345",
                quantidade=2,
                operator="admin",
                notes="Entrega dupla autorizada",
            )
            db.session.add(delivery_log)
            db.session.commit()

            # Verify delivery log was created
            saved_log = DeliveryLog.query.first()
            assert saved_log is not None
            assert saved_log.participant_id == sample_participant.id
            assert saved_log.item_id == sample_delivery_item.id
            assert saved_log.matricula == "12345"
            assert saved_log.quantidade == 2
            assert saved_log.operator == "admin"
            assert saved_log.notes == "Entrega dupla autorizada"
            assert saved_log.status == "delivered"  # Default value
            assert saved_log.delivery_time is not None

    def test_delivery_log_relationships(
        self, test_app, sample_participant, sample_delivery_item
    ):
        """Test delivery log relationships."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.add(sample_delivery_item)
            db.session.flush()

            delivery_log = DeliveryLog(
                participant_id=sample_participant.id,
                item_id=sample_delivery_item.id,
                quantidade=1,
            )
            db.session.add(delivery_log)
            db.session.commit()

            # Test relationships
            saved_log = DeliveryLog.query.first()
            assert saved_log.participant.nome == "João Silva"
            assert saved_log.item.nome == "Cesta Básica"

            # Test back-references
            participant = Participant.query.first()
            assert len(participant.deliveries) == 1

            item = DeliveryItem.query.first()
            assert len(item.delivery_logs) == 1


class TestEmailLog:
    """Test cases for EmailLog model."""

    def test_email_log_creation(self, test_app, sample_participant):
        """Test creating a new email log."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.flush()

            email_log = EmailLog(
                participant_id=sample_participant.id,
                email_type="qr_delivery",
                subject="Seu QR Code para o evento BUNDOKAI",
                status="sent",
            )
            db.session.add(email_log)
            db.session.commit()

            # Verify email log was created
            saved_log = EmailLog.query.first()
            assert saved_log is not None
            assert saved_log.participant_id == sample_participant.id
            assert saved_log.email_type == "qr_delivery"
            assert saved_log.subject == "Seu QR Code para o evento BUNDOKAI"
            assert saved_log.status == "sent"
            assert saved_log.sent_at is not None
            assert saved_log.opened_at is None  # Not opened yet

    def test_email_log_opened_tracking(self, test_app, sample_participant):
        """Test email opened tracking."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.flush()

            email_log = EmailLog(
                participant_id=sample_participant.id,
                email_type="reminder",
                subject="Lembrete do evento",
                status="sent",
            )
            db.session.add(email_log)
            db.session.commit()

            # Simulate email being opened
            saved_log = EmailLog.query.first()
            saved_log.opened_at = datetime.utcnow()
            db.session.commit()

            # Verify opened tracking
            updated_log = EmailLog.query.first()
            assert updated_log.opened_at is not None

    def test_email_log_relationship(self, test_app, sample_participant):
        """Test email log participant relationship."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.flush()

            email_log = EmailLog(
                participant_id=sample_participant.id,
                email_type="confirmation",
                subject="Confirmação de inscrição",
            )
            db.session.add(email_log)
            db.session.commit()

            # Test relationship
            saved_log = EmailLog.query.first()
            assert saved_log.participant_email.nome == "João Silva"

            participant = Participant.query.first()
            assert len(participant.emails) == 1
            assert participant.emails[0].email_type == "confirmation"


class TestModelIntegration:
    """Integration tests for multiple models working together."""

    def test_complete_participant_workflow(self, test_app):
        """Test a complete participant workflow with all related models."""
        with test_app.app_context():
            # Create participant
            participant = Participant(
                nome="Ana Santos",
                email="ana.santos@lightera.com",
                telefone="11888777666",
                departamento="RH",
                matricula="54321",
                qr_code="QR654321",
            )
            db.session.add(participant)
            db.session.flush()

            # Add dependents
            dependent1 = Dependent(
                nome="Lucas Santos", idade=10, participant_id=participant.id
            )
            dependent2 = Dependent(
                nome="Carla Santos", idade=6, participant_id=participant.id
            )
            db.session.add(dependent1)
            db.session.add(dependent2)

            # Send QR code email
            qr_email = EmailLog(
                participant_id=participant.id,
                email_type="qr_delivery",
                subject="Seu QR Code - BUNDOKAI 2024",
                status="sent",
            )
            db.session.add(qr_email)

            # Participant arrives and checks in
            checkin = CheckIn(
                participant_id=participant.id,
                station="entrance_a",
                operator="security_01",
            )
            db.session.add(checkin)

            # Create delivery items
            cesta = DeliveryItem(
                nome="Cesta de Natal",
                categoria="Festa",
                estoque_inicial=200,
                estoque_atual=199,
                preco_unitario=75.0,
            )
            brinquedo = DeliveryItem(
                nome="Kit Brinquedos",
                categoria="Brinquedos",
                estoque_inicial=150,
                estoque_atual=148,
                preco_unitario=30.0,
            )
            db.session.add(cesta)
            db.session.add(brinquedo)
            db.session.flush()

            # Participant picks up items
            delivery1 = DeliveryLog(
                participant_id=participant.id,
                item_id=cesta.id,
                matricula="54321",
                quantidade=1,
                operator="delivery_admin",
            )
            delivery2 = DeliveryLog(
                participant_id=participant.id,
                item_id=brinquedo.id,
                matricula="54321",
                quantidade=2,  # One for each child
                operator="delivery_admin",
            )
            db.session.add(delivery1)
            db.session.add(delivery2)

            db.session.commit()

            # Verify complete workflow
            saved_participant = Participant.query.filter_by(
                email="ana.santos@lightera.com"
            ).first()
            assert saved_participant is not None
            assert len(saved_participant.dependents) == 2
            assert len(saved_participant.checkins) == 1
            assert len(saved_participant.deliveries) == 2
            assert len(saved_participant.emails) == 1

            # Verify check-in details
            assert saved_participant.checkins[0].station == "entrance_a"
            assert saved_participant.checkins[0].operator == "security_01"

            # Verify deliveries
            total_items_delivered = sum(
                d.quantidade for d in saved_participant.deliveries
            )
            assert total_items_delivered == 3  # 1 cesta + 2 brinquedos

            # Verify email tracking
            assert saved_participant.emails[0].email_type == "qr_delivery"
            assert saved_participant.emails[0].status == "sent"
