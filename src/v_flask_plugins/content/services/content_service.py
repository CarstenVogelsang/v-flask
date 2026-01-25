"""Content rendering and management service."""
import json
from pathlib import Path
from typing import Any

from flask import render_template, current_app
from markupsafe import Markup


class ContentService:
    """Service for content block rendering and management."""

    def __init__(self):
        self._intentions_cache: list[dict] | None = None
        self._layouts_cache: list[dict] | None = None

    def _get_data_path(self) -> Path:
        """Get the path to the data directory."""
        return Path(__file__).parent.parent / 'data'

    def get_intentions(self) -> list[dict]:
        """Load available intentions from JSON.

        Returns:
            List of intention definitions with id, name, beschreibung, layouts
        """
        if self._intentions_cache is not None:
            return self._intentions_cache

        intentions_path = self._get_data_path() / 'intentions.json'
        try:
            with open(intentions_path, 'r', encoding='utf-8') as f:
                self._intentions_cache = json.load(f)
        except FileNotFoundError:
            current_app.logger.warning(f'intentions.json not found at {intentions_path}')
            self._intentions_cache = []

        return self._intentions_cache

    def get_layouts(self) -> list[dict]:
        """Load available layouts from JSON.

        Returns:
            List of layout definitions with id, name, felder, template
        """
        if self._layouts_cache is not None:
            return self._layouts_cache

        layouts_path = self._get_data_path() / 'layouts.json'
        try:
            with open(layouts_path, 'r', encoding='utf-8') as f:
                self._layouts_cache = json.load(f)
        except FileNotFoundError:
            current_app.logger.warning(f'layouts.json not found at {layouts_path}')
            self._layouts_cache = []

        return self._layouts_cache

    def get_intention_by_id(self, intention_id: str) -> dict | None:
        """Get a specific intention by ID."""
        intentions = self.get_intentions()
        for intention in intentions:
            if intention.get('id') == intention_id:
                return intention
        return None

    def get_layout_by_id(self, layout_id: str) -> dict | None:
        """Get a specific layout by ID."""
        layouts = self.get_layouts()
        for layout in layouts:
            if layout.get('id') == layout_id:
                return layout
        return None

    def get_layouts_for_intention(self, intention_id: str) -> list[dict]:
        """Get available layouts for a specific intention.

        Args:
            intention_id: The intention ID to filter by

        Returns:
            List of layout definitions available for this intention
        """
        intention = self.get_intention_by_id(intention_id)
        if not intention:
            return []

        allowed_layout_ids = intention.get('layouts', [])
        all_layouts = self.get_layouts()

        return [
            layout for layout in all_layouts
            if layout.get('id') in allowed_layout_ids
        ]

    def render_content_block(self, content_block: Any) -> str:
        """Render a content block to HTML.

        Args:
            content_block: ContentBlock model instance

        Returns:
            Rendered HTML string
        """
        if not content_block or not content_block.active:
            return ''

        layout = self.get_layout_by_id(content_block.layout)
        if not layout:
            current_app.logger.warning(
                f'Layout {content_block.layout} not found for ContentBlock {content_block.id}'
            )
            return ''

        # Prepare context for rendering
        context = {
            'block': content_block,
            'titel': content_block.titel,
            'text': content_block.text,
            'bilder': content_block.bilder,
            'content_data': content_block.content_data or {},
        }

        # Get first image if available - load actual Media object
        if content_block.bilder:
            from v_flask_plugins.media.models import Media
            bild_data = content_block.bilder[0]
            media_id = bild_data.get('media_id')
            if media_id:
                media = Media.query.get(media_id)
                context['bild'] = media  # Pass Media object, not dict
                context['bild_data'] = bild_data  # Keep original dict if needed
            else:
                context['bild'] = None
                context['bild_data'] = bild_data
        else:
            context['bild'] = None
            context['bild_data'] = None

        # Render the layout template
        template_name = f"content/{layout.get('template', 'layouts/nur_text.html')}"
        try:
            return render_template(template_name, **context)
        except Exception as e:
            current_app.logger.error(
                f'Error rendering ContentBlock {content_block.id}: {e}'
            )
            return ''

    def render_slot(self, endpoint: str, slot: str) -> str:
        """Render all content blocks for a specific slot on a page.

        Args:
            endpoint: The Flask endpoint (e.g., 'public.index')
            slot: The slot position (e.g., 'after_content')

        Returns:
            Combined HTML of all matching content blocks
        """
        from v_flask.content_slots.models import PageRoute
        from v_flask_plugins.content.models import ContentAssignment

        # Find the page route
        page_route = PageRoute.query.filter_by(endpoint=endpoint).first()
        if not page_route:
            return ''

        # Get all active assignments for this page and slot
        assignments = (
            ContentAssignment.query
            .filter_by(
                page_route_id=page_route.id,
                slot_position=slot,
                active=True
            )
            .order_by(
                ContentAssignment.priority.desc(),
                ContentAssignment.sort_order.asc()
            )
            .all()
        )

        if not assignments:
            return ''

        # Render each content block
        rendered_blocks = []
        for assignment in assignments:
            if assignment.content_block and assignment.content_block.active:
                html = self.render_content_block(assignment.content_block)
                if html:
                    rendered_blocks.append(html)

        return Markup('\n'.join(rendered_blocks))

    def clear_cache(self) -> None:
        """Clear the intentions and layouts cache."""
        self._intentions_cache = None
        self._layouts_cache = None


# Singleton instance
content_service = ContentService()
