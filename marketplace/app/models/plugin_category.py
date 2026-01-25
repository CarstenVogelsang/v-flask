"""Plugin category model for organizing plugins."""
from v_flask import db


class PluginCategory(db.Model):
    """Predefined plugin categories for filtering and organization.

    Categories are seeded via CLI command and provide visual grouping
    for the plugin list in admin interface.
    """

    __tablename__ = 'marketplace_plugin_category'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name_de = db.Column(db.String(50), nullable=False)
    description_de = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=False)  # Tabler icon class, e.g. "ti ti-shield-check"
    color_hex = db.Column(db.String(7), nullable=False)  # Hex color, e.g. "#22c55e"
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f'<PluginCategory {self.code}>'

    @classmethod
    def get_all_ordered(cls) -> list['PluginCategory']:
        """Get all categories ordered by sort_order."""
        return cls.query.order_by(cls.sort_order).all()

    @classmethod
    def get_by_code(cls, code: str) -> 'PluginCategory | None':
        """Get category by code."""
        return cls.query.filter_by(code=code).first()
