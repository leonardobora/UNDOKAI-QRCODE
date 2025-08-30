# Overview

Lightera BUNDOKAI is a comprehensive event management system designed to replace the costly Digitevent solution (R$ 5,427.00) for corporate events at Furukawa Electric/Lightera. The system handles participant registration, QR code generation, check-in management, and end-of-year delivery tracking for up to 2,500 participants. It features a multi-functional approach combining event check-in capabilities with inventory management for corporate deliveries across different categories (party supplies, gift baskets, toys, school materials).

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
The system is built on Flask (Python 3.8+) with SQLAlchemy ORM for database operations. The architecture follows a modular design pattern with separate modules for models, routes, and utilities. The database layer uses SQLite for development and production environments, optimized for the expected 2,500-participant scale. The backend implements RESTful API patterns for frontend communication and includes comprehensive logging and error handling throughout.

## Database Design
The data model centers around five core entities: Participant (main user data with unique QR codes), Dependent (family members, up to 5 per participant), CheckIn (event attendance tracking), DeliveryItem (inventory management), and DeliveryLog (delivery tracking). The schema supports one-to-many relationships between participants and their dependents/check-ins, with proper foreign key constraints and cascade deletion policies. Email tracking is handled through an EmailLog model for audit trails and delivery confirmation.

## Frontend Architecture
The frontend uses a traditional server-side rendered approach with Jinja2 templates, enhanced by Bootstrap 5 for responsive design and vanilla JavaScript for interactive features. The scanner functionality leverages HTML5-QRCode library for camera-based QR code reading, while the search functionality implements debounced AJAX requests for real-time participant lookup. The dashboard provides real-time statistics through periodic AJAX updates and includes Chart.js for data visualization.

## QR Code System
QR code generation utilizes the Python qrcode library with Pillow for image processing. Each participant receives a unique 8-character alphanumeric code that serves as their event identifier. The system generates base64-encoded QR images for email delivery and provides both camera-based scanning and manual code entry for check-in flexibility. The QR validation system includes duplicate check-in prevention and audit logging.

## Email Integration
The email system supports SMTP configuration for automated QR code delivery and event reminders. Templates are HTML-based with embedded QR code images, supporting both batch sending and individual delivery. The system includes delivery tracking, bounce handling, and configurable scheduling for pre-event communications. Email logs maintain comprehensive audit trails for compliance purposes.

## Security and Data Protection
The system implements session-based authentication with CSRF protection and includes LGPD compliance features for data handling. Database operations use parameterized queries to prevent SQL injection, while user inputs undergo validation and sanitization. The system maintains detailed audit logs for all participant interactions and includes data export/import capabilities for backup and migration purposes.

# External Dependencies

## Core Framework Dependencies
- **Flask 2.3.3**: Web application framework providing routing, templating, and session management
- **Flask-SQLAlchemy 3.0.5**: Database ORM integration for model definition and query operations
- **Werkzeug**: WSGI utilities and middleware for production deployment

## QR Code and Image Processing
- **qrcode[pil] 7.4.2**: QR code generation library with PIL image support for creating participant access codes
- **Pillow 10.0.1**: Image processing library for QR code rendering and manipulation
- **HTML5-QRCode**: Frontend JavaScript library for camera-based QR code scanning (CDN-delivered)

## Data Processing and Export
- **pandas 2.1.1**: Data manipulation library for Excel import/export and report generation
- **python-dotenv 1.0.0**: Environment variable management for configuration

## Frontend Libraries (CDN)
- **Bootstrap 5.3.0**: Responsive CSS framework for UI components and layouts
- **Font Awesome 6.0.0**: Icon library for consistent visual elements
- **Chart.js**: Data visualization library for dashboard analytics

## Production Deployment
- **gunicorn 21.2.0**: WSGI HTTP server for production deployment
- **ProxyFix middleware**: Handles reverse proxy headers for production environments

## Email and Communication
- **SMTP libraries**: Built-in Python smtplib for email delivery with configurable providers
- **Email template system**: HTML template processing for QR code delivery and reminders

## Development and Testing
- **opencv-python-headless 4.8.1.78**: Computer vision library for advanced QR processing capabilities
- **SQLite**: Embedded database system optimized for the expected participant volume

## Optional External Services
- **Email providers**: Configurable SMTP integration (Gmail, corporate email servers)
- **File storage**: Local filesystem for QR code images, reports, and uploads
- **Backup systems**: Database export capabilities for data protection and migration