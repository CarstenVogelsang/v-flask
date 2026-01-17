"""Public shop routes for plugin catalog.

Displays available plugins with descriptions and pricing.
"""
from flask import Blueprint, render_template

from v_flask import db
from app.models import PluginMeta

shop_bp = Blueprint(
    'shop',
    __name__,
    template_folder='../templates/shop'
)


@shop_bp.route('/')
def plugin_list():
    """Display all published plugins."""
    plugins = db.session.query(PluginMeta).filter_by(
        is_published=True
    ).order_by(
        PluginMeta.is_featured.desc(),
        PluginMeta.name
    ).all()

    return render_template('plugin_list.html', plugins=plugins)


@shop_bp.route('/<plugin_name>')
def plugin_detail(plugin_name: str):
    """Display plugin details."""
    plugin = db.session.query(PluginMeta).filter_by(
        name=plugin_name,
        is_published=True
    ).first_or_404()

    return render_template('plugin_detail.html', plugin=plugin)
