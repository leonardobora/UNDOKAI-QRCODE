from functools import wraps

from flask import flash, redirect, session, url_for
from werkzeug.security import check_password_hash


def login_required(f):
    """Decorator to require admin login"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session or not session["admin_logged_in"]:
            flash(
                "Por favor, faça login como administrador para acessar esta página.",
                "warning",
            )
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)

    return decorated_function


def check_admin_credentials(username, password):
    """Check if admin credentials are valid"""
    # Hardcoded admin credentials as requested
    ADMIN_USERNAME = "lightera"
    ADMIN_PASSWORD = "admin"

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True
    return False


def is_admin():
    """Check if current user is logged in as admin"""
    return session.get("admin_logged_in", False)
