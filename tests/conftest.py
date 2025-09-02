"""
Test configuration and fixtures for Lightera BUNDOKAI system.
"""
import pytest
import tempfile
import os
from datetime import datetime

# Add the parent directory to the path so we can import our app modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Participant, Dependent, CheckIn, DeliveryItem, DeliveryLog, EmailLog


@pytest.fixture
def test_app():
    """Create and configure a test Flask application."""
    # Create a temporary file for the test database
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    # Create application context
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # Clean up temporary file
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


@pytest.fixture
def client(test_app):
    """Create a test client for the Flask application."""
    return test_app.test_client()


@pytest.fixture
def runner(test_app):
    """Create a test runner for the Flask application."""
    return test_app.test_cli_runner()


@pytest.fixture
def sample_participant():
    """Create a sample participant for testing."""
    participant = Participant(
        nome="João Silva",
        email="joao.silva@lightera.com",
        telefone="11999887766",
        departamento="TI",
        matricula="12345",
        qr_code="QR123456"
    )
    return participant


@pytest.fixture
def sample_dependent():
    """Create a sample dependent for testing."""
    dependent = Dependent(
        nome="Maria Silva",
        idade=8
    )
    return dependent


@pytest.fixture
def sample_delivery_item():
    """Create a sample delivery item for testing."""
    item = DeliveryItem(
        nome="Cesta Básica",
        categoria="Cesta Básica",
        descricao="Cesta com produtos básicos para final de ano",
        estoque_inicial=100,
        estoque_atual=100,
        preco_unitario=50.0
    )
    return item


@pytest.fixture
def db_with_data(test_app):
    """Create a database with sample data for testing."""
    with test_app.app_context():
        # Create a participant with dependents
        participant = Participant(
            nome="João Silva",
            email="joao.silva@lightera.com",
            telefone="11999887766", 
            departamento="TI",
            matricula="12345",
            qr_code="QR123456"
        )
        db.session.add(participant)
        db.session.flush()  # Flush to get the participant ID
        
        # Add dependents
        dependent1 = Dependent(nome="Maria Silva", idade=8, participant_id=participant.id)
        dependent2 = Dependent(nome="Pedro Silva", idade=12, participant_id=participant.id)
        db.session.add(dependent1)
        db.session.add(dependent2)
        
        # Add delivery items
        item1 = DeliveryItem(
            nome="Cesta Básica",
            categoria="Cesta Básica",
            descricao="Cesta com produtos básicos",
            estoque_inicial=100,
            estoque_atual=95,
            preco_unitario=50.0
        )
        item2 = DeliveryItem(
            nome="Kit Escolar",
            categoria="Material Escolar",
            descricao="Kit com material escolar completo",
            estoque_inicial=50,
            estoque_atual=45,
            preco_unitario=25.0
        )
        db.session.add(item1)
        db.session.add(item2)
        db.session.flush()
        
        # Add a check-in
        checkin = CheckIn(
            participant_id=participant.id,
            station="main",
            operator="admin"
        )
        db.session.add(checkin)
        
        # Add a delivery log
        delivery = DeliveryLog(
            participant_id=participant.id,
            item_id=item1.id,
            matricula="12345",
            quantidade=1,
            operator="admin",
            notes="Entrega realizada com sucesso"
        )
        db.session.add(delivery)
        
        # Add an email log
        email_log = EmailLog(
            participant_id=participant.id,
            email_type="qr_delivery",
            subject="Seu QR Code para o evento BUNDOKAI",
            status="sent"
        )
        db.session.add(email_log)
        
        db.session.commit()
        
        return {
            'participant': participant,
            'dependents': [dependent1, dependent2],
            'items': [item1, item2],
            'checkin': checkin,
            'delivery': delivery,
            'email_log': email_log
        }