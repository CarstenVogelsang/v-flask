"""Shop plugin routes."""

from v_flask_plugins.shop.routes.admin import shop_admin_bp
from v_flask_plugins.shop.routes.auth import shop_auth_bp
from v_flask_plugins.shop.routes.public import shop_public_bp

__all__ = ['shop_auth_bp', 'shop_public_bp', 'shop_admin_bp']
