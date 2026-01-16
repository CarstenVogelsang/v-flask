"""Admin navigation categories.

Defines the standard categories for organizing plugin admin pages
in the sidebar navigation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class AdminCategory:
    """Definition of an admin navigation category."""

    id: str
    label: str
    icon: str
    order: int


# Standard admin categories that plugins can use
# Plugins specify their category via admin_category = 'legal' etc.
ADMIN_CATEGORIES: dict[str, dict] = {
    'core': {
        'label': 'Dashboard',
        'icon': 'ti ti-dashboard',
        'order': 0,
    },
    'directory': {
        'label': 'Verzeichnis',
        'icon': 'ti ti-map-pin',
        'order': 10,
    },
    'content': {
        'label': 'Inhalte',
        'icon': 'ti ti-article',
        'order': 20,
    },
    'legal': {
        'label': 'Rechtliches',
        'icon': 'ti ti-shield-check',
        'order': 30,
    },
    'communication': {
        'label': 'Kommunikation',
        'icon': 'ti ti-messages',
        'order': 40,
    },
    'marketing': {
        'label': 'Marketing',
        'icon': 'ti ti-speakerphone',
        'order': 50,
    },
    'users': {
        'label': 'Benutzer',
        'icon': 'ti ti-users',
        'order': 60,
    },
    'analytics': {
        'label': 'Analytics',
        'icon': 'ti ti-chart-bar',
        'order': 70,
    },
    'ecommerce': {
        'label': 'E-Commerce',
        'icon': 'ti ti-shopping-cart',
        'order': 80,
    },
    'system': {
        'label': 'System',
        'icon': 'ti ti-settings',
        'order': 100,
    },
}


def get_category(category_id: str) -> dict | None:
    """Get category definition by ID.

    Args:
        category_id: Category identifier (e.g., 'legal', 'system')

    Returns:
        Category dict with label, icon, order or None if not found.
    """
    return ADMIN_CATEGORIES.get(category_id)


def get_sorted_categories() -> list[tuple[str, dict]]:
    """Get all categories sorted by order.

    Returns:
        List of (category_id, category_dict) tuples sorted by order.
    """
    return sorted(
        ADMIN_CATEGORIES.items(),
        key=lambda x: x[1]['order']
    )


def register_category(
    category_id: str,
    label: str,
    icon: str,
    order: int = 50,
) -> None:
    """Register a custom admin category.

    Host apps can register additional categories beyond the defaults.

    Args:
        category_id: Unique identifier for the category
        label: Display label (e.g., 'Mein Bereich')
        icon: Tabler icon class (e.g., 'ti ti-star')
        order: Sort order (lower = earlier, default 50)

    Example:
        register_category('my_section', 'Mein Bereich', 'ti ti-star', order=35)
    """
    ADMIN_CATEGORIES[category_id] = {
        'label': label,
        'icon': icon,
        'order': order,
    }
