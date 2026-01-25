"""CTA Service for rendering and managing CTA sections.

Provides the main business logic for:
- Rendering CTA sections with Jinja2 placeholders
- Finding CTAs assigned to routes
- Managing the placeholder context
"""

from __future__ import annotations

from typing import Any

from flask import current_app, render_template
from jinja2 import Template

from v_flask.extensions import db


# Default values for platform placeholders
PLATTFORM_CONFIG_DEFAULTS = {
    'name': 'v-flask',
    'zielgruppe': 'Café, Restaurant oder Hotel',
    'location_bezeichnung': 'Lokal',
}

# Available placeholders for CTA templates
AVAILABLE_PLACEHOLDERS = [
    '{{ plattform.name }}',
    '{{ plattform.zielgruppe }}',
    '{{ location.bezeichnung }}',
    '{{ ort.name }}',
    '{{ kreis.name }}',
    '{{ bundesland.name }}',
]

# Preview context for live preview in admin
PREVIEW_CONTEXT = {
    'ort': {'name': 'Kleve'},
    'kreis': {'name': 'Kreis Kleve'},
    'bundesland': {'name': 'Nordrhein-Westfalen'},
}


class CtaService:
    """Service for CTA rendering and management.

    Handles:
    - Loading CTA sections from database
    - Rendering Jinja2 placeholders
    - Finding CTAs for specific routes and slots
    - Managing platform configuration
    """

    def __init__(self) -> None:
        """Initialize the CTA service."""
        self._plattform_cache: dict | None = None

    @property
    def plattform(self) -> dict:
        """Get platform configuration (lazy loaded with cache).

        Loads from:
        1. CTA plugin settings
        2. Betreiber model (fallback)
        3. Default values (fallback)

        Returns:
            Dict with name, zielgruppe, location_bezeichnung.
        """
        if self._plattform_cache is not None:
            return self._plattform_cache

        self._plattform_cache = self._load_plattform_config()
        return self._plattform_cache

    def invalidate_cache(self) -> None:
        """Invalidate the platform configuration cache."""
        self._plattform_cache = None

    def _load_plattform_config(self) -> dict:
        """Load platform configuration from settings or Betreiber.

        Returns:
            Dict with platform configuration.
        """
        config = PLATTFORM_CONFIG_DEFAULTS.copy()

        try:
            # Try loading from CTA plugin settings
            from v_flask.models import PluginConfig
            plugin_config = PluginConfig.query.filter_by(plugin_name='cta').first()

            if plugin_config and plugin_config.settings:
                settings = plugin_config.settings
                if settings.get('plattform_name'):
                    config['name'] = settings['plattform_name']
                if settings.get('plattform_zielgruppe'):
                    config['zielgruppe'] = settings['plattform_zielgruppe']
                if settings.get('location_bezeichnung'):
                    config['location_bezeichnung'] = settings['location_bezeichnung']
                return config
        except Exception:
            pass

        try:
            # Fallback: Load from Betreiber model
            from v_flask.models import Betreiber
            betreiber = Betreiber.query.first()

            if betreiber:
                if betreiber.name:
                    config['name'] = betreiber.name
                # Check for custom settings
                if hasattr(betreiber, 'get_setting'):
                    zielgruppe = betreiber.get_setting('plattform_zielgruppe')
                    if zielgruppe:
                        config['zielgruppe'] = zielgruppe
                    location_bez = betreiber.get_setting('location_bezeichnung')
                    if location_bez:
                        config['location_bezeichnung'] = location_bez
        except Exception:
            pass

        return config

    def _build_context(self, context: dict[str, Any] | None = None) -> dict:
        """Build the full rendering context.

        Combines:
        - Platform configuration (static)
        - User-provided context (dynamic, e.g., ort, kreis)

        Args:
            context: Optional user-provided context.

        Returns:
            Complete context dict for Jinja2 rendering.
        """
        plattform = self.plattform

        full_context = {
            'plattform': {
                'name': plattform['name'],
                'zielgruppe': plattform['zielgruppe'],
            },
            'location': {
                'bezeichnung': plattform['location_bezeichnung'],
            },
        }

        # Add user context (doesn't override platform keys)
        if context:
            for key, value in context.items():
                if key not in ('plattform', 'location'):
                    full_context[key] = value

        return full_context

    def _render_text(self, text: str, context: dict) -> str:
        """Render text with Jinja2 placeholders.

        Args:
            text: Text with placeholders.
            context: Context dict for rendering.

        Returns:
            Rendered text string.
        """
        if not text:
            return ''

        try:
            return Template(text).render(context)
        except Exception:
            # Return original text if rendering fails
            return text

    def get_cta_by_slug(self, slug: str) -> Any | None:
        """Get a CTA template by slug.

        Args:
            slug: Template slug.

        Returns:
            CtaTemplate instance or None.
        """
        from v_flask_plugins.cta.models import CtaTemplate
        return CtaTemplate.query.filter_by(slug=slug, active=True).first()

    def get_cta_for_route(
        self,
        endpoint: str,
        slot: str = 'after_content',
    ) -> Any | None:
        """Find CTA section assigned to a route and slot.

        Args:
            endpoint: Flask endpoint name.
            slot: Slot position.

        Returns:
            CtaSection instance or None.
        """
        from v_flask_plugins.cta.models import CtaSection, CtaAssignment
        from v_flask.content_slots.models import PageRoute

        assignment = (
            db.session.query(CtaAssignment)
            .join(PageRoute)
            .join(CtaSection)
            .filter(
                PageRoute.endpoint == endpoint,
                CtaAssignment.slot_position == slot,
                CtaAssignment.active == True,  # noqa: E712
                CtaSection.active == True,  # noqa: E712
            )
            .order_by(CtaAssignment.priority.desc())
            .first()
        )

        if assignment:
            return assignment.cta_section

        return None

    def render_cta(
        self,
        cta: Any,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render a CTA section as HTML.

        Args:
            cta: CtaSection instance.
            context: Additional context for placeholders.

        Returns:
            Rendered HTML string.
        """
        full_context = self._build_context(context)

        # Render title and description with placeholders
        rendered_title = self._render_text(cta.title, full_context)
        rendered_description = self._render_text(cta.description, full_context)

        # Select template based on variant
        template_path = f'cta/variants/{cta.variant}.html'

        try:
            return render_template(
                template_path,
                cta=cta,
                title=rendered_title,
                description=rendered_description,
                cta_text=cta.cta_text,
                cta_link=cta.cta_link,
            )
        except Exception as e:
            current_app.logger.error(f'CTA render error: {e}')
            return ''

    def render_cta_slot(
        self,
        endpoint: str,
        slot: str = 'after_content',
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render CTA for a specific endpoint and slot.

        Args:
            endpoint: Flask endpoint name.
            slot: Slot position.
            context: Additional context for placeholders.

        Returns:
            Rendered HTML string or empty string.
        """
        cta = self.get_cta_for_route(endpoint, slot)

        if not cta:
            return ''

        return self.render_cta(cta, context)

    def render_preview(
        self,
        titel: str,
        beschreibung: str,
        variant: str = 'card',
    ) -> dict[str, str]:
        """Render a preview for the admin editor.

        Uses preview context with sample values.

        Args:
            titel: Title text with placeholders.
            beschreibung: Description text with placeholders.
            variant: Design variant.

        Returns:
            Dict with rendered title and description.
        """
        context = self._build_context(PREVIEW_CONTEXT)

        return {
            'titel': self._render_text(titel, context),
            'beschreibung': self._render_text(beschreibung, context),
        }

    def get_assignable_routes(
        self,
        exclude_blueprints: list[str] | None = None,
    ) -> list:
        """Get routes that can have CTAs assigned.

        Args:
            exclude_blueprints: Blueprints to exclude.

        Returns:
            List of PageRoute instances.
        """
        from v_flask.content_slots.models import PageRoute

        query = PageRoute.query.filter_by(hero_assignable=True)

        if exclude_blueprints:
            query = query.filter(~PageRoute.blueprint.in_(exclude_blueprints))

        return query.order_by(PageRoute.display_name, PageRoute.endpoint).all()

    def assign_cta_to_route(
        self,
        cta_id: int,
        route_id: int,
        slot: str = 'after_content',
        priority: int = 50,
    ) -> Any | None:
        """Assign a CTA section to a page route.

        Creates or updates the assignment.

        Args:
            cta_id: CtaSection ID.
            route_id: PageRoute ID.
            slot: Slot position.
            priority: Priority (higher = preferred).

        Returns:
            CtaAssignment instance or None on error.
        """
        from v_flask_plugins.cta.models import CtaSection, CtaAssignment
        from v_flask.content_slots.models import PageRoute

        cta = db.session.get(CtaSection, cta_id)
        route = db.session.get(PageRoute, route_id)

        if not cta or not route:
            return None

        # Check for existing assignment
        existing = CtaAssignment.query.filter_by(
            page_route_id=route_id,
            slot_position=slot,
        ).first()

        if existing:
            # Update existing
            existing.cta_section_id = cta_id
            existing.priority = priority
            existing.active = True
        else:
            # Create new
            existing = CtaAssignment(
                cta_section_id=cta_id,
                page_route_id=route_id,
                slot_position=slot,
                priority=priority,
            )
            db.session.add(existing)

        db.session.commit()
        return existing


# Singleton instance
cta_service = CtaService()


__all__ = ['CtaService', 'cta_service', 'AVAILABLE_PLACEHOLDERS', 'PREVIEW_CONTEXT']
