#!/usr/bin/env python3
"""
Generate Sample Data for Lightera UNDOKAI
Creates realistic test participants and dependents for development/testing
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import random
import uuid
from datetime import datetime, timedelta

from app import app, db
from models import CheckIn, DeliveryItem, DeliveryLog, Dependent, EmailLog, Participant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample data
DEPARTMENTS = [
    "Tecnologia da Informação",
    "Recursos Humanos",
    "Vendas",
    "Marketing",
    "Financeiro",
    "Operações",
    "Qualidade",
    "Engenharia",
    "Logística",
    "Diretoria",
]

FIRST_NAMES = [
    "Ana",
    "Antonio",
    "Beatriz",
    "Carlos",
    "Daniela",
    "Eduardo",
    "Fernanda",
    "Gabriel",
    "Helena",
    "Igor",
    "Julia",
    "Leandro",
    "Mariana",
    "Nicolas",
    "Olivia",
    "Pedro",
    "Rafaela",
    "Rodrigo",
    "Sofia",
    "Thiago",
    "Valentina",
    "William",
    "Yasmin",
    "Zara",
]

LAST_NAMES = [
    "Silva",
    "Santos",
    "Oliveira",
    "Souza",
    "Rodrigues",
    "Ferreira",
    "Alves",
    "Pereira",
    "Lima",
    "Gomes",
    "Costa",
    "Ribeiro",
    "Martins",
    "Carvalho",
    "Almeida",
    "Lopes",
    "Soares",
    "Fernandes",
    "Vieira",
    "Barbosa",
    "Rocha",
    "Dias",
    "Monteiro",
    "Cardoso",
]

DEPENDENT_NAMES = [
    "João",
    "Maria",
    "José",
    "Ana",
    "Antonio",
    "Francisca",
    "Carlos",
    "Paulo",
    "Lucas",
    "Luiza",
    "Miguel",
    "Alice",
    "Arthur",
    "Laura",
    "Gabriel",
    "Manuela",
    "Rafael",
    "Isabela",
    "Guilherme",
    "Helena",
    "Mateus",
    "Valentina",
    "Nicolas",
    "Sophia",
]


def generate_participant_data(count=100):
    """Generate realistic participant data"""
    participants = []

    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"

        # Generate email based on name
        email_name = f"{first_name.lower()}.{last_name.lower()}"
        email = f"{email_name}@lightera.com"

        # Generate phone
        phone = f"(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"

        # Select department
        department = random.choice(DEPARTMENTS)

        # Generate QR code
        qr_code = str(uuid.uuid4())[:8].upper()

        participant_data = {
            "nome": full_name,
            "email": email,
            "telefone": phone,
            "departamento": department,
            "qr_code": qr_code,
        }

        # Generate dependents (0-3 per participant)
        dependent_count = random.choices([0, 1, 2, 3], weights=[30, 40, 20, 10])[0]
        dependents = []

        for j in range(dependent_count):
            dependent_name = random.choice(DEPENDENT_NAMES)
            dependent_age = random.randint(0, 18)

            dependents.append({"nome": dependent_name, "idade": dependent_age})

        participants.append({"participant": participant_data, "dependents": dependents})

    return participants


def create_participants(participant_data_list):
    """Create participants and dependents in database"""
    created_participants = []

    try:
        with app.app_context():
            for data in participant_data_list:
                # Check if participant already exists
                existing = Participant.query.filter_by(
                    email=data["participant"]["email"]
                ).first()
                if existing:
                    logger.info(
                        f"Participant {data['participant']['nome']} already exists, skipping..."
                    )
                    continue

                # Create participant
                participant = Participant(**data["participant"])
                db.session.add(participant)
                db.session.flush()  # Get the ID

                # Create dependents
                for dep_data in data["dependents"]:
                    dependent = Dependent(
                        nome=dep_data["nome"],
                        idade=dep_data["idade"],
                        participant_id=participant.id,
                    )
                    db.session.add(dependent)

                created_participants.append(participant)

                if len(created_participants) % 10 == 0:
                    logger.info(f"Created {len(created_participants)} participants...")

            db.session.commit()
            logger.info(
                f"Successfully created {len(created_participants)} participants"
            )

            return created_participants

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create participants: {str(e)}")
        return []


def create_sample_checkins(participants, percentage=30):
    """Create check-ins for a percentage of participants"""
    try:
        with app.app_context():
            checkin_count = int(len(participants) * (percentage / 100))
            selected_participants = random.sample(participants, checkin_count)

            stations = ["main", "scanner", "manual-search", "entrance-1", "entrance-2"]

            created_checkins = []

            for participant in selected_participants:
                # Random check-in time within the last 8 hours
                hours_ago = random.randint(1, 8)
                minutes_ago = random.randint(0, 59)
                checkin_time = datetime.now() - timedelta(
                    hours=hours_ago, minutes=minutes_ago
                )

                checkin = CheckIn(
                    participant_id=participant.id,
                    checkin_time=checkin_time,
                    station=random.choice(stations),
                    operator="Sistema",
                )

                db.session.add(checkin)
                created_checkins.append(checkin)

            db.session.commit()
            logger.info(f"Created {len(created_checkins)} sample check-ins")

            return created_checkins

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create check-ins: {str(e)}")
        return []


def create_sample_deliveries(participants, items):
    """Create sample delivery logs"""
    try:
        with app.app_context():
            # Select 20% of participants for deliveries
            delivery_count = int(len(participants) * 0.2)
            selected_participants = random.sample(participants, delivery_count)

            operators = ["João Silva", "Maria Santos", "Carlos Oliveira", "Ana Costa"]

            created_deliveries = []

            for participant in selected_participants:
                # Each participant gets 1-3 items
                item_count = random.randint(1, 3)
                selected_items = random.sample(items, min(item_count, len(items)))

                for item in selected_items:
                    # Random delivery time within last 3 days
                    days_ago = random.randint(0, 3)
                    hours_ago = random.randint(0, 23)
                    delivery_time = datetime.now() - timedelta(
                        days=days_ago, hours=hours_ago
                    )

                    delivery = DeliveryLog(
                        participant_id=participant.id,
                        item_id=item.id,
                        delivery_time=delivery_time,
                        quantidade=1,
                        status="delivered",
                        operator=random.choice(operators),
                    )

                    db.session.add(delivery)
                    created_deliveries.append(delivery)

                    # Update item stock
                    item.estoque_atual = max(0, item.estoque_atual - 1)

            db.session.commit()
            logger.info(f"Created {len(created_deliveries)} sample deliveries")

            return created_deliveries

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create deliveries: {str(e)}")
        return []


def create_sample_emails(participants):
    """Create sample email logs"""
    try:
        with app.app_context():
            email_types = ["qr_delivery", "reminder", "confirmation"]
            statuses = ["sent", "opened", "failed"]

            created_emails = []

            for participant in participants:
                # Each participant gets 1-2 emails
                email_count = random.randint(1, 2)

                for _ in range(email_count):
                    email_type = random.choice(email_types)
                    status = random.choices(statuses, weights=[70, 25, 5])[0]

                    # Random sent time within last week
                    days_ago = random.randint(0, 7)
                    hours_ago = random.randint(0, 23)
                    sent_time = datetime.now() - timedelta(
                        days=days_ago, hours=hours_ago
                    )

                    subject_map = {
                        "qr_delivery": "UNDOKAI 2024 - Seu QR Code de Acesso",
                        "reminder": "UNDOKAI 2024 - Lembrete do Evento",
                        "confirmation": "UNDOKAI 2024 - Confirmação de Inscrição",
                    }

                    email_log = EmailLog(
                        participant_id=participant.id,
                        email_type=email_type,
                        subject=subject_map[email_type],
                        sent_at=sent_time,
                        status=status,
                        opened_at=(
                            sent_time + timedelta(hours=random.randint(1, 48))
                            if status == "opened"
                            else None
                        ),
                    )

                    db.session.add(email_log)
                    created_emails.append(email_log)

            db.session.commit()
            logger.info(f"Created {len(created_emails)} sample email logs")

            return created_emails

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create email logs: {str(e)}")
        return []


def generate_statistics():
    """Generate and display statistics"""
    try:
        with app.app_context():
            stats = {
                "participants": Participant.query.count(),
                "dependents": Dependent.query.count(),
                "checkins": CheckIn.query.count(),
                "delivery_items": DeliveryItem.query.count(),
                "deliveries": DeliveryLog.query.count(),
                "emails": EmailLog.query.count(),
            }

            logger.info("\n" + "=" * 50)
            logger.info("LIGHTERA UNDOKAI - DATABASE STATISTICS")
            logger.info("=" * 50)
            logger.info(f"👥 Participants: {stats['participants']}")
            logger.info(f"👶 Dependents: {stats['dependents']}")
            logger.info(f"✅ Check-ins: {stats['checkins']}")
            logger.info(f"📦 Delivery Items: {stats['delivery_items']}")
            logger.info(f"🚚 Deliveries: {stats['deliveries']}")
            logger.info(f"📧 Emails: {stats['emails']}")

            # Calculate attendance rate
            if stats["participants"] > 0:
                attendance_rate = (stats["checkins"] / stats["participants"]) * 100
                logger.info(f"📊 Attendance Rate: {attendance_rate:.1f}%")

            logger.info("=" * 50)

            return stats

    except Exception as e:
        logger.error(f"Failed to generate statistics: {str(e)}")
        return {}


def main():
    """Main data generation function"""
    logger.info("Starting sample data generation for Lightera UNDOKAI...")

    # Generate participant data
    logger.info("Generating participant data...")
    participant_data = generate_participant_data(count=150)

    # Create participants
    logger.info("Creating participants in database...")
    participants = create_participants(participant_data)

    if not participants:
        logger.error("Failed to create participants!")
        sys.exit(1)

    # Get delivery items
    with app.app_context():
        items = DeliveryItem.query.all()

    if not items:
        logger.warning("No delivery items found. Run setup_database.py first.")

    # Create sample check-ins (30% of participants)
    logger.info("Creating sample check-ins...")
    checkins = create_sample_checkins(participants, percentage=30)

    # Create sample deliveries
    if items:
        logger.info("Creating sample deliveries...")
        deliveries = create_sample_deliveries(participants, items)

    # Create sample emails
    logger.info("Creating sample email logs...")
    emails = create_sample_emails(participants)

    # Generate statistics
    stats = generate_statistics()

    logger.info("Sample data generation completed successfully!")
    logger.info("You can now start the application and see realistic test data.")


if __name__ == "__main__":
    main()
