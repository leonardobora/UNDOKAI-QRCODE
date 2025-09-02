#!/usr/bin/env python3
"""
Database Setup Script for Lightera UNDOKAI
Creates database tables and initial configuration
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

from app import app, db
from models import CheckIn, DeliveryItem, DeliveryLog, Dependent, EmailLog, Participant
from utils import create_sample_delivery_items

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database():
    """Initialize database with tables and sample data"""
    try:
        with app.app_context():
            # Drop all tables (use with caution in production)
            logger.info("Dropping existing tables...")
            db.drop_all()

            # Create all tables
            logger.info("Creating database tables...")
            db.create_all()

            # Create sample delivery items
            logger.info("Creating sample delivery items...")
            create_sample_delivery_items()

            # Verify tables were created
            tables = db.engine.table_names()
            logger.info(f"Created tables: {', '.join(tables)}")

            # Print table counts
            participant_count = Participant.query.count()
            delivery_item_count = DeliveryItem.query.count()

            logger.info(f"Database setup complete!")
            logger.info(f"- Participants: {participant_count}")
            logger.info(f"- Delivery Items: {delivery_item_count}")

            return True

    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False


def create_admin_user():
    """Create a default admin user for testing"""
    try:
        with app.app_context():
            # Check if admin user already exists
            admin = Participant.query.filter_by(email="admin@lightera.com").first()

            if admin:
                logger.info("Admin user already exists")
                return admin

            # Create admin user
            admin = Participant(
                nome="Administrador Sistema",
                email="admin@lightera.com",
                telefone="(11) 99999-9999",
                departamento="TI",
                qr_code="ADMIN123",
            )

            db.session.add(admin)
            db.session.commit()

            logger.info(f"Admin user created with QR Code: {admin.qr_code}")
            return admin

    except Exception as e:
        logger.error(f"Failed to create admin user: {str(e)}")
        return None


def verify_database():
    """Verify database integrity and constraints"""
    try:
        with app.app_context():
            logger.info("Verifying database integrity...")

            # Test participant creation
            test_participant = Participant(
                nome="Test User", email="test@example.com", qr_code="TEST123"
            )

            db.session.add(test_participant)
            db.session.flush()

            # Test dependent creation
            test_dependent = Dependent(
                nome="Test Dependent", idade=10, participant_id=test_participant.id
            )

            db.session.add(test_dependent)
            db.session.commit()

            # Verify relationships
            assert test_participant.dependents[0].nome == "Test Dependent"
            assert test_dependent.participant.nome == "Test User"

            # Clean up test data
            db.session.delete(test_dependent)
            db.session.delete(test_participant)
            db.session.commit()

            logger.info("Database verification passed!")
            return True

    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        db.session.rollback()
        return False


def main():
    """Main setup function"""
    logger.info("Starting Lightera UNDOKAI database setup...")

    # Setup database
    if not setup_database():
        logger.error("Database setup failed!")
        sys.exit(1)

    # Create admin user
    admin = create_admin_user()
    if not admin:
        logger.warning("Failed to create admin user")

    # Verify database
    if not verify_database():
        logger.error("Database verification failed!")
        sys.exit(1)

    logger.info("Database setup completed successfully!")
    logger.info("You can now start the application with: python app.py")

    if admin:
        logger.info(f"Admin QR Code for testing: {admin.qr_code}")


if __name__ == "__main__":
    main()
