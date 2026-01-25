"""CTA Slot Provider for the Content Slot System.

This module provides the CtaSlotProvider class that integrates
the CTA plugin with the v-flask content slot system.

Usage:
    from v_flask_plugins.cta.slot_provider import CtaSlotProvider
    from v_flask import content_slot_registry

    content_slot_registry.register(CtaSlotProvider())
"""

from __future__ import annotations

from typing import Any

from v_flask.content_slots import ContentSlotProvider


class CtaSlotProvider(ContentSlotProvider):
    """Content slot provider for CTA sections.

    Provides CTA content for multiple slots based on route assignments.
    Uses the CtaAssignment model to determine which CTA section
    to render for each endpoint.

    Attributes:
        name: Provider name ('cta').
        priority: Medium priority (50) - CTAs come after heroes.
        slots: Handles after_content, floating, sidebar slots.
    """

    name = 'cta'
    priority = 50  # Lower than hero (100) - CTAs after heroes
    slots = ['after_content', 'floating', 'sidebar', 'before_content', 'footer']

    def render(
        self,
        endpoint: str,
        slot: str,
        context: dict[str, Any],
    ) -> str | None:
        """Render CTA section for the given endpoint and slot.

        Looks up the CtaAssignment for this endpoint and slot,
        then renders the assigned CtaSection using the cta_service.

        Args:
            endpoint: Flask endpoint name (e.g., 'public.index').
            slot: Slot position (e.g., 'after_content').
            context: Template context with additional data (ort, kreis, etc.).

        Returns:
            Rendered HTML string, or None if no CTA is assigned.
        """
        if slot not in self.slots:
            return None

        from v_flask_plugins.cta.services.cta_service import cta_service

        # Use the CTA service to render
        result = cta_service.render_cta_slot(endpoint, slot, context)

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
        return slot in self.slots


# Singleton instance for import
cta_slot_provider = CtaSlotProvider()


__all__ = ['CtaSlotProvider', 'cta_slot_provider']
