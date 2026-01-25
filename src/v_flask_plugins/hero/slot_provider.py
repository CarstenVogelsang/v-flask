"""Hero Slot Provider for the Content Slot System.

This module provides the HeroSlotProvider class that integrates
the Hero plugin with the v-flask content slot system.

Usage:
    from v_flask_plugins.hero.slot_provider import HeroSlotProvider
    from v_flask import content_slot_registry

    content_slot_registry.register(HeroSlotProvider())
"""

from __future__ import annotations

from typing import Any

from v_flask.content_slots import ContentSlotProvider


class HeroSlotProvider(ContentSlotProvider):
    """Content slot provider for Hero sections.

    Provides hero content for the 'top' slot based on route assignments.
    Uses the HeroAssignment model to determine which hero section
    to render for each endpoint.

    Attributes:
        name: Provider name ('hero').
        priority: High priority (100) - heroes are typically the main content.
        slots: Only handles the 'top' slot.
    """

    name = 'hero'
    priority = 100  # High priority - hero is the main banner
    slots = ['top']  # Hero sections go in the 'top' slot

    def render(
        self,
        endpoint: str,
        slot: str,
        context: dict[str, Any],
    ) -> str | None:
        """Render hero section for the given endpoint and slot.

        Looks up the HeroAssignment for this endpoint and slot,
        then renders the assigned HeroSection using the hero_service.

        Args:
            endpoint: Flask endpoint name (e.g., 'public.index').
            slot: Slot position (expected: 'top').
            context: Template context with additional data.

        Returns:
            Rendered HTML string, or None if no hero is assigned.
        """
        if slot != 'top':
            return None

        from v_flask_plugins.hero.services.hero_service import hero_service

        # Map 'top' to 'hero_top' for internal hero slot naming
        hero_slot = 'hero_top'

        # Use the existing hero service to render
        result = hero_service.render_hero_slot(endpoint, hero_slot)

        if result:
            return result

        return None

    def can_render(self, endpoint: str, slot: str) -> bool:
        """Check if this provider might have content for the slot.

        Quick check before full render - avoids database queries
        for slots we don't handle.

        Args:
            endpoint: Flask endpoint name.
            slot: Slot position.

        Returns:
            True if we handle this slot, False otherwise.
        """
        return slot == 'top'


# Singleton instance for import
hero_slot_provider = HeroSlotProvider()


__all__ = ['HeroSlotProvider', 'hero_slot_provider']
