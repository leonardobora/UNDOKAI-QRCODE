"""
Unit tests for utility functions.
"""

import base64
import io
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app import db
from models import CheckIn, DeliveryItem, Dependent, Participant
from utils import (
    create_sample_delivery_items,
    generate_qr_code,
    get_checkin_statistics,
    send_qr_email,
)


class TestQRCodeGeneration:
    """Test cases for QR code generation utilities."""

    def test_generate_qr_code_basic(self):
        """Test basic QR code generation."""
        data = "TEST123"
        qr_result = generate_qr_code(data)

        # Should return a data URL
        assert qr_result.startswith("data:image/png;base64,")

        # Extract base64 data and verify it's valid
        base64_data = qr_result.split(",")[1]
        img_data = base64.b64decode(base64_data)

        # Should be able to create a PIL image from the data
        img_buffer = io.BytesIO(img_data)
        img = Image.open(img_buffer)
        assert img.format == "PNG"
        assert img.size[0] > 0  # Width should be positive
        assert img.size[1] > 0  # Height should be positive

    def test_generate_qr_code_custom_size(self):
        """Test QR code generation with custom size."""
        data = "TEST456"
        qr_small = generate_qr_code(data, size=5, border=2)
        qr_large = generate_qr_code(data, size=15, border=6)

        # Both should be valid base64 PNG data
        assert qr_small.startswith("data:image/png;base64,")
        assert qr_large.startswith("data:image/png;base64,")

        # Large QR should have more data (larger file)
        small_data = qr_small.split(",")[1]
        large_data = qr_large.split(",")[1]
        assert len(large_data) > len(small_data)

    def test_generate_qr_code_different_data(self):
        """Test QR code generation with different data produces different results."""
        qr1 = generate_qr_code("DATA1")
        qr2 = generate_qr_code("DATA2")

        # Should be different QR codes
        assert qr1 != qr2

        # But both should be valid
        assert qr1.startswith("data:image/png;base64,")
        assert qr2.startswith("data:image/png;base64,")

    def test_generate_qr_code_unicode(self):
        """Test QR code generation with unicode characters."""
        data = "Olá, Mundo! 🎉"
        qr_result = generate_qr_code(data)

        # Should handle unicode without errors
        assert qr_result.startswith("data:image/png;base64,")


class TestEmailSending:
    """Test cases for email sending utilities."""

    @patch("utils.smtplib.SMTP")
    @patch.dict(
        "os.environ",
        {
            "SMTP_SERVER": "test.smtp.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test@lightera.com",
            "SMTP_PASSWORD": "testpass",
        },
    )
    def test_send_qr_email_success(self, mock_smtp, test_app, sample_participant):
        """Test successful email sending."""
        with test_app.app_context():
            # Mock SMTP server
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Add sample participant to database
            db.session.add(sample_participant)
            db.session.commit()

            # Test email sending
            result = send_qr_email(sample_participant)

            # Should return True for success
            assert result is True

            # Verify SMTP calls
            mock_smtp.assert_called_once_with("test.smtp.com", 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("test@lightera.com", "testpass")
            mock_server.send_message.assert_called_once()

    @patch("utils.smtplib.SMTP")
    @patch.dict(
        "os.environ",
        {
            "SMTP_SERVER": "test.smtp.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test@lightera.com",
            "SMTP_PASSWORD": "testpass",
        },
    )
    def test_send_qr_email_with_image(self, mock_smtp, test_app, sample_participant):
        """Test email sending with QR code image attachment."""
        with test_app.app_context():
            # Mock SMTP server
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Add sample participant to database
            db.session.add(sample_participant)
            db.session.commit()

            # Generate a test QR code image
            qr_image = generate_qr_code("TEST123")

            # Test email sending with image
            result = send_qr_email(sample_participant, qr_image)

            # Should return True for success
            assert result is True

            # Verify SMTP calls
            mock_server.send_message.assert_called_once()

            # The message should include the attachment
            call_args = mock_server.send_message.call_args[0][0]
            assert call_args.is_multipart()  # Should be multipart with attachment

    @patch.dict("os.environ", {}, clear=True)
    def test_send_qr_email_no_credentials(self, test_app, sample_participant):
        """Test email sending without credentials configured."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.commit()

            # Should return False when credentials not configured
            result = send_qr_email(sample_participant)
            assert result is False

    @patch("utils.smtplib.SMTP")
    @patch.dict(
        "os.environ",
        {
            "SMTP_SERVER": "test.smtp.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test@lightera.com",
            "SMTP_PASSWORD": "testpass",
        },
    )
    def test_send_qr_email_smtp_error(self, mock_smtp, test_app, sample_participant):
        """Test email sending with SMTP error."""
        with test_app.app_context():
            # Mock SMTP server to raise an exception
            mock_smtp.side_effect = Exception("SMTP connection failed")

            db.session.add(sample_participant)
            db.session.commit()

            # Should return False on SMTP error
            result = send_qr_email(sample_participant)
            assert result is False


class TestSampleDataCreation:
    """Test cases for sample data creation utilities."""

    def test_create_sample_delivery_items(self, test_app):
        """Test creating sample delivery items."""
        with test_app.app_context():
            # Initially no delivery items
            assert DeliveryItem.query.count() == 0

            # Create sample items
            create_sample_delivery_items()

            # Should have created multiple items
            items = DeliveryItem.query.all()
            assert len(items) > 0

            # Verify categories are created
            categories = set(item.categoria for item in items)
            expected_categories = {
                "Festa",
                "Cesta Básica",
                "Brinquedos",
                "Material Escolar",
            }
            assert expected_categories.issubset(categories)

            # Verify specific items exist
            festa_items = DeliveryItem.query.filter_by(categoria="Festa").all()
            assert len(festa_items) >= 3

            cesta_items = DeliveryItem.query.filter_by(categoria="Cesta Básica").all()
            assert len(cesta_items) >= 2

            brinquedo_items = DeliveryItem.query.filter_by(categoria="Brinquedos").all()
            assert len(brinquedo_items) >= 3

            escolar_items = DeliveryItem.query.filter_by(
                categoria="Material Escolar"
            ).all()
            assert len(escolar_items) >= 3

    def test_create_sample_delivery_items_no_duplicates(self, test_app):
        """Test that creating sample items doesn't create duplicates."""
        with test_app.app_context():
            # Create sample items twice
            create_sample_delivery_items()
            initial_count = DeliveryItem.query.count()

            create_sample_delivery_items()
            final_count = DeliveryItem.query.count()

            # Count should remain the same (no duplicates)
            assert initial_count == final_count

    def test_sample_delivery_items_structure(self, test_app):
        """Test the structure of created sample delivery items."""
        with test_app.app_context():
            create_sample_delivery_items()

            items = DeliveryItem.query.all()

            for item in items:
                # Every item should have required fields
                assert item.nome is not None and len(item.nome) > 0
                assert item.categoria is not None and len(item.categoria) > 0
                assert item.estoque_inicial >= 0
                assert item.estoque_atual >= 0
                assert (
                    item.estoque_inicial == item.estoque_atual
                )  # Initial stock should equal current
                assert item.created_at is not None


class TestStatistics:
    """Test cases for statistics utilities."""

    def test_get_checkin_statistics_empty(self, test_app):
        """Test statistics with no data."""
        with test_app.app_context():
            stats = get_checkin_statistics()

            assert stats["total_participants"] == 0
            assert stats["total_checkins"] == 0
            assert stats["total_dependents"] == 0
            assert stats["pending_checkins"] == 0
            assert stats["department_stats"] == {}
            assert len(stats["hourly_checkins"]) == 24  # Should have 24 hours
            assert all(
                hour_data["count"] == 0 for hour_data in stats["hourly_checkins"]
            )

    def test_get_checkin_statistics_with_data(self, test_app, db_with_data):
        """Test statistics with sample data."""
        with test_app.app_context():
            data = db_with_data
            stats = get_checkin_statistics()

            # Should reflect the data we created
            assert stats["total_participants"] == 1
            assert stats["total_checkins"] == 1
            assert stats["total_dependents"] == 2
            assert stats["pending_checkins"] == 0  # 1 participant, 1 checkin

            # Department stats should include our participant's department
            assert "TI" in stats["department_stats"]
            assert stats["department_stats"]["TI"] == 1

            # Hourly checkins should have 24 entries
            assert len(stats["hourly_checkins"]) == 24
            assert all(
                "hour" in hour_data and "count" in hour_data
                for hour_data in stats["hourly_checkins"]
            )

    def test_get_checkin_statistics_multiple_departments(self, test_app):
        """Test statistics with multiple departments."""
        with test_app.app_context():
            # Create participants from different departments
            participants = [
                Participant(
                    nome="João TI",
                    email="joao@lightera.com",
                    departamento="TI",
                    qr_code="QR001",
                ),
                Participant(
                    nome="Maria RH",
                    email="maria@lightera.com",
                    departamento="RH",
                    qr_code="QR002",
                ),
                Participant(
                    nome="Pedro TI",
                    email="pedro@lightera.com",
                    departamento="TI",
                    qr_code="QR003",
                ),
                Participant(
                    nome="Ana Vendas",
                    email="ana@lightera.com",
                    departamento="Vendas",
                    qr_code="QR004",
                ),
            ]

            for participant in participants:
                db.session.add(participant)
            db.session.flush()

            # Add some check-ins
            checkins = [
                CheckIn(participant_id=participants[0].id),  # João TI
                CheckIn(participant_id=participants[2].id),  # Pedro TI
                CheckIn(participant_id=participants[3].id),  # Ana Vendas
            ]

            for checkin in checkins:
                db.session.add(checkin)
            db.session.commit()

            stats = get_checkin_statistics()

            # Verify department breakdown
            assert stats["total_participants"] == 4
            assert stats["total_checkins"] == 3
            assert stats["pending_checkins"] == 1  # Maria RH hasn't checked in

            dept_stats = stats["department_stats"]
            assert dept_stats["TI"] == 2
            assert dept_stats["RH"] == 1
            assert dept_stats["Vendas"] == 1

    def test_get_checkin_statistics_with_dependents(self, test_app):
        """Test statistics calculation with dependents."""
        with test_app.app_context():
            # Create participant with multiple dependents
            participant = Participant(
                nome="Família Silva",
                email="familia@lightera.com",
                departamento="Admin",
                qr_code="QR001",
            )
            db.session.add(participant)
            db.session.flush()

            # Add dependents
            dependents = [
                Dependent(nome="Filho 1", idade=8, participant_id=participant.id),
                Dependent(nome="Filho 2", idade=12, participant_id=participant.id),
                Dependent(nome="Filho 3", idade=5, participant_id=participant.id),
            ]

            for dependent in dependents:
                db.session.add(dependent)
            db.session.commit()

            stats = get_checkin_statistics()

            assert stats["total_participants"] == 1
            assert stats["total_dependents"] == 3
            assert stats["total_checkins"] == 0  # No check-ins yet
            assert stats["pending_checkins"] == 1


class TestUtilityIntegration:
    """Integration tests for utility functions working together."""

    @patch("utils.smtplib.SMTP")
    @patch.dict(
        "os.environ",
        {
            "SMTP_SERVER": "test.smtp.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test@lightera.com",
            "SMTP_PASSWORD": "testpass",
        },
    )
    def test_complete_qr_workflow(self, mock_smtp, test_app):
        """Test complete QR code generation and email workflow."""
        with test_app.app_context():
            # Mock SMTP server
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Create participant
            participant = Participant(
                nome="Test User", email="test@lightera.com", qr_code="QR_TEST_001"
            )
            db.session.add(participant)
            db.session.commit()

            # Generate QR code
            qr_image = generate_qr_code(participant.qr_code)
            assert qr_image.startswith("data:image/png;base64,")

            # Send email with QR code
            result = send_qr_email(participant, qr_image)
            assert result is True

            # Verify email was sent
            mock_server.send_message.assert_called_once()

            # Get statistics
            stats = get_checkin_statistics()
            assert stats["total_participants"] == 1
            assert stats["total_checkins"] == 0  # No check-in yet
            assert stats["pending_checkins"] == 1

    def test_data_consistency_after_operations(self, test_app):
        """Test data consistency after various utility operations."""
        with test_app.app_context():
            # Create sample delivery items
            create_sample_delivery_items()
            initial_item_count = DeliveryItem.query.count()

            # Create participants and check-ins
            participants = []
            for i in range(5):
                participant = Participant(
                    nome=f"User {i+1}",
                    email=f"user{i+1}@lightera.com",
                    departamento="Test",
                    qr_code=f"QR{i+1:03d}",
                )
                participants.append(participant)
                db.session.add(participant)
            db.session.flush()

            # Add some check-ins
            for i in range(3):  # Only 3 out of 5 check in
                checkin = CheckIn(participant_id=participants[i].id)
                db.session.add(checkin)
            db.session.commit()

            # Get statistics and verify consistency
            stats = get_checkin_statistics()
            assert stats["total_participants"] == 5
            assert stats["total_checkins"] == 3
            assert stats["pending_checkins"] == 2

            # Verify delivery items weren't affected
            assert DeliveryItem.query.count() == initial_item_count

            # Create sample items again - should not create duplicates
            create_sample_delivery_items()
            assert DeliveryItem.query.count() == initial_item_count
