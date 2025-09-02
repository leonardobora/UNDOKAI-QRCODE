import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

def create_app():
    """Factory function to create the Flask app"""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "lightera-bundokai-secret-key-2024")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///bundokai.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize the database extension
    db = SQLAlchemy(model_class=Base)
    db.init_app(app)
    
    with app.app_context():
        # Import and initialize models
        from models import init_models
        init_models(db)
        
        # Import routes
        from routes import register_routes
        register_routes(app, db)
        
        # Create all database tables
        db.create_all()
    
    return app, db

# Create the app and database for direct import
app, db = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)