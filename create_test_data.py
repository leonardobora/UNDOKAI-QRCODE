#!/usr/bin/env python3
"""
Create sample data for testing the UNDOKAI system
"""

import random
from datetime import datetime, timedelta

from app import app, db
from models import CheckIn, Dependent, Participant


def create_sample_data():
    """Create sample participants and check-ins"""
    with app.app_context():
        # Clear existing data for demo
        db.session.query(CheckIn).delete()
        db.session.query(Dependent).delete()
        db.session.query(Participant).delete()
        db.session.commit()

        # Sample departments
        departments = [
            "TI",
            "RH",
            "Financeiro",
            "Marketing",
            "Vendas",
            "Operações",
            "Administração",
        ]

        # Create sample participants
        participants_data = [
            ("João Silva", "joao.silva@lightera.com.br", "11987654321", "TI"),
            ("Maria Santos", "maria.santos@lightera.com.br", "11876543210", "RH"),
            (
                "Carlos Oliveira",
                "carlos.oliveira@lightera.com.br",
                "11765432109",
                "Financeiro",
            ),
            ("Ana Costa", "ana.costa@lightera.com.br", "11654321098", "Marketing"),
            ("Pedro Mendes", "pedro.mendes@lightera.com.br", "11543210987", "TI"),
            (
                "Lucia Ferreira",
                "lucia.ferreira@lightera.com.br",
                "11432109876",
                "Vendas",
            ),
            (
                "Roberto Lima",
                "roberto.lima@lightera.com.br",
                "11321098765",
                "Operações",
            ),
            ("Patricia Souza", "patricia.souza@lightera.com.br", "11210987654", "RH"),
            (
                "Fernando Alves",
                "fernando.alves@lightera.com.br",
                "11109876543",
                "Administração",
            ),
            (
                "Camila Rocha",
                "camila.rocha@lightera.com.br",
                "11098765432",
                "Marketing",
            ),
            ("Marcos Pereira", "marcos.pereira@lightera.com.br", "11987654320", "TI"),
            (
                "Julia Nascimento",
                "julia.nascimento@lightera.com.br",
                "11876543209",
                "Financeiro",
            ),
            (
                "Ricardo Barbosa",
                "ricardo.barbosa@lightera.com.br",
                "11765432108",
                "Vendas",
            ),
            (
                "Isabela Martins",
                "isabela.martins@lightera.com.br",
                "11654321097",
                "Operações",
            ),
            ("Bruno Carvalho", "bruno.carvalho@lightera.com.br", "11543210986", "RH"),
        ]

        participants = []
        for i, (nome, email, telefone, dept) in enumerate(participants_data):
            participant = Participant(
                nome=nome,
                email=email,
                telefone=telefone,
                departamento=dept,
                matricula=f"EMP{1000 + i}",
                qr_code=f"UND2025{1000 + i}",
            )
            participants.append(participant)
            db.session.add(participant)

        db.session.commit()

        # Create some dependents
        dependent_names = [
            "Ana Silva Jr.",
            "Pedro Santos Jr.",
            "Maria Oliveira Jr.",
            "João Costa Jr.",
            "Lucia Mendes Jr.",
            "Carlos Ferreira Jr.",
        ]

        for i, name in enumerate(dependent_names):
            if i < len(participants):
                dependent = Dependent(
                    nome=name,
                    idade=random.randint(5, 15),
                    participant_id=participants[i].id,
                )
                db.session.add(dependent)

        db.session.commit()

        # Create some check-ins (about 60% of participants)
        checked_in_count = int(len(participants) * 0.6)
        checked_in_participants = random.sample(participants, checked_in_count)

        # Create check-ins throughout the day
        base_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        stations = ["main", "entrance", "scanner-1", "scanner-2", "manual-search"]

        for i, participant in enumerate(checked_in_participants):
            # Spread check-ins across the morning
            checkin_time = base_time + timedelta(
                minutes=random.randint(0, 240)
            )  # 4 hours spread
            checkin = CheckIn(
                participant_id=participant.id,
                checkin_time=checkin_time,
                station=random.choice(stations),
                operator=random.choice(["Scanner QR", "Manual", "Sistema", "Admin"]),
            )
            db.session.add(checkin)

        db.session.commit()

        print(f"✅ Created {len(participants)} participants")
        print(f"✅ Created {len(dependent_names)} dependents")
        print(f"✅ Created {checked_in_count} check-ins")
        print(
            f"📊 Attendance rate: {(checked_in_count / len(participants)) * 100:.1f}%"
        )


if __name__ == "__main__":
    create_sample_data()
