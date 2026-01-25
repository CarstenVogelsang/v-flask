"""Content slot provider for rendering content blocks in page slots."""
from typing import Any

from v_flask.content_slots import ContentSlotProvider


class ContentSlotProvider(ContentSlotProvider):
    """Slot provider for content blocks.

    This provider renders content blocks assigned to pages via
    ContentAssignment into the appropriate slots.
    """

    name = 'content'
    priority = 40  # Lower than hero (100) and cta (50)
    slots = ['before_content', 'after_content', 'sidebar']

    def render(self, endpoint: str, slot: str, context: dict[str, Any]) -> str | None:
        """Render content blocks for a slot.

        Args:
            endpoint: The Flask endpoint (e.g., 'public.index')
            slot: The slot position (e.g., 'after_content')
            context: Additional context from the page

        Returns:
            Rendered HTML or None if no content for this slot
        """
        if slot not in self.slots:
            return None

        from v_flask_plugins.content.services.content_service import content_service

        html = content_service.render_slot(endpoint, slot)
        return html if html else None

    def can_render(self, endpoint: str, slot: str) -> bool:
        """Check if this provider can render for the given slot.

        Args:
            endpoint: The Flask endpoint
            slot: The slot position

        Returns:
            True if this provider handles the slot
        """
        if slot not in self.slots:
            return False

        # Quick check if there are any assignments for this endpoint/slot
        from v_flask.content_slots.models import PageRoute
        from v_flask_plugins.content.models import ContentAssignment

        page_route = PageRoute.query.filter_by(endpoint=endpoint).first()
        if not page_route:
            return False

        return ContentAssignment.query.filter_by(
            page_route_id=page_route.id,
            slot_position=slot,
            active=True
        ).first() is not None


# Singleton instance for registration
content_slot_provider = ContentSlotProvider()
