"""Marketplace routes."""
from app.routes.admin import admin_bp
from app.routes.shop import shop_bp
from app.routes.api import api_bp

__all__ = ['admin_bp', 'shop_bp', 'api_bp']
