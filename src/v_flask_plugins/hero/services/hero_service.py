"""Hero Section service for rendering and template processing.

Provides business logic for hero sections including:
- Template rendering with Jinja2 placeholders
- Active hero section retrieval
- Live preview for admin UI
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from flask import render_template_string
from jinja2 import Template

from v_flask.extensions import db

if TYPE_CHECKING:
    from v_flask.models import Betreiber
    from v_flask_plugins.hero.models import HeroSection, HeroTemplate


class HeroService:
    """Service class for hero section operations.

    Handles rendering of hero sections with dynamic template
    placeholders like {{ betreiber.name }}.

    Usage:
        from v_flask_plugins.hero.services.hero_service import HeroService

        service = HeroService()

        # Get rendered HTML for active hero
        html = service.render_active_hero()

        # Preview template with custom text
        preview = service.render_preview('Titel', 'Untertitel')
    """

    def __init__(self):
        """Initialize the hero service."""
        self._betreiber: Betreiber | None = None

    @property
    def betreiber(self) -> Betreiber | None:
        """Get cached Betreiber instance.

        Returns:
            Betreiber instance or None if not configured.
        """
        if self._betreiber is None:
            from v_flask.models import Betreiber
            self._betreiber = db.session.query(Betreiber).first()
        return self._betreiber

    def _build_context(self, extra_context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build context for template rendering.

        Args:
            extra_context: Additional context to merge.

        Returns:
            Complete context dictionary with betreiber data.
        """
        context = {}

        if self.betreiber:
            context['betreiber'] = {
                'name': self.betreiber.name,
                'website': self.betreiber.website,
                'email': self.betreiber.email,
            }
            # Also provide 'plattform' for compatibility with existing templates
            context['plattform'] = context['betreiber']

        # Provide fallback for 'location' if not in extra_context
        # This prevents template errors when {{ location.bezeichnung }} is used
        # on pages without a location context (e.g., homepage, contact page)
        if not extra_context or 'location' not in extra_context:
            # Get location_bezeichnung from Betreiber settings (configured in admin)
            location_bezeichnung = 'Lokal'  # Default fallback
            if self.betreiber:
                location_bezeichnung = self.betreiber.get_setting(
                    'location_bezeichnung', 'Lokal'
                )

            context['location'] = {
                'bezeichnung': location_bezeichnung,
                'name': '',
            }

        if extra_context:
            context.update(extra_context)

        return context

    # ==============================================
    # Hero Section Methods
    # ==============================================

    def get_active_hero(self) -> HeroSection | None:
        """Get the active hero section.

        Returns:
            Active HeroSection or None if none configured.
        """
        from v_flask_plugins.hero.models import HeroSection
        return HeroSection.query.filter_by(active=True).first()

    def render_active_hero(self, extra_context: dict[str, Any] | None = None) -> str:
        """Render the active hero section as HTML.

        Args:
            extra_context: Additional context for template rendering.

        Returns:
            Rendered HTML string, or empty string if no active hero.
        """
        hero = self.get_active_hero()
        if not hero:
            return ''

        return self.render_hero(hero, extra_context)

    def render_hero(
        self,
        hero: HeroSection,
        extra_context: dict[str, Any] | None = None
    ) -> str:
        """Render a specific hero section as HTML.

        Args:
            hero: HeroSection instance to render.
            extra_context: Additional context for template rendering.

        Returns:
            Rendered HTML string.
        """
        context = self._build_context(extra_context)

        # Render title and subtitle (may contain Jinja2 placeholders)
        rendered_title = self._render_text(hero.title, context)
        rendered_subtitle = self._render_text(hero.subtitle, context)

        # Render the appropriate template variant
        template_path = f'hero/{hero.variant}.html'

        try:
            from flask import render_template
            return render_template(
                template_path,
                hero=hero,
                title=rendered_title,
                subtitle=rendered_subtitle,
            )
        except Exception:
            # Fallback if template not found
            return self._render_fallback(hero, rendered_title, rendered_subtitle)

    def _render_text(self, text: str, context: dict[str, Any]) -> str:
        """Render text with Jinja2 placeholders.

        Args:
            text: Text potentially containing placeholders.
            context: Context dictionary for rendering.

        Returns:
            Rendered text string.
        """
        if not text:
            return ''

        try:
            return Template(text).render(context)
        except Exception:
            # Return raw text if rendering fails
            return text

    def _render_fallback(
        self,
        hero: HeroSection,
        title: str,
        subtitle: str
    ) -> str:
        """Render a fallback hero section if template is missing.

        Args:
            hero: HeroSection instance.
            title: Rendered title.
            subtitle: Rendered subtitle.

        Returns:
            Simple HTML fallback.
        """
        fallback_html = '''
        <section class="hero bg-base-200 py-20">
            <div class="text-center">
                {% if title %}<h1 class="text-4xl font-bold">{{ title }}</h1>{% endif %}
                {% if subtitle %}<p class="py-6 text-lg">{{ subtitle }}</p>{% endif %}
                {% if hero.cta_text and hero.cta_link %}
                <a href="{{ hero.cta_link }}" class="btn btn-primary">
                    {{ hero.cta_text }}
                </a>
                {% endif %}
            </div>
        </section>
        '''
        return render_template_string(
            fallback_html,
            hero=hero,
            title=title,
            subtitle=subtitle
        )

    # ==============================================
    # Template Methods
    # ==============================================

    def get_template(self, template_id: int) -> HeroTemplate | None:
        """Get HeroTemplate by ID.

        Args:
            template_id: Template ID.

        Returns:
            HeroTemplate or None if not found.
        """
        from v_flask_plugins.hero.models import HeroTemplate
        return HeroTemplate.query.get(template_id)

    def get_default_template(self) -> HeroTemplate | None:
        """Get the default HeroTemplate.

        Returns:
            Default HeroTemplate or None if none set.
        """
        from v_flask_plugins.hero.models import HeroTemplate
        return HeroTemplate.query.filter_by(is_default=True, active=True).first()

    def get_all_templates(self) -> list[HeroTemplate]:
        """Get all active HeroTemplates.

        Returns:
            List of active HeroTemplates, default first.
        """
        from v_flask_plugins.hero.models import HeroTemplate
        return HeroTemplate.query.filter_by(active=True).order_by(
            HeroTemplate.is_default.desc(),
            HeroTemplate.name
        ).all()

    def render_template(
        self,
        template_id: int | None = None
    ) -> dict[str, str] | None:
        """Render HeroTemplate with betreiber context.

        Args:
            template_id: Template ID. If None, uses default.

        Returns:
            Dict with rendered 'titel' and 'untertitel', or None.
        """
        if template_id:
            template = self.get_template(template_id)
        else:
            template = self.get_default_template()

        if not template:
            return None

        context = self._build_context()

        try:
            titel = Template(template.titel).render(context)
            untertitel = Template(template.untertitel).render(context)
        except Exception:
            titel = template.titel
            untertitel = template.untertitel

        return {'titel': titel, 'untertitel': untertitel}

    # ==============================================
    # Preview Methods (for Admin UI)
    # ==============================================

    def render_preview(
        self,
        titel: str,
        untertitel: str
    ) -> dict[str, str]:
        """Render preview text with betreiber context.

        Used in admin UI for live preview.

        Args:
            titel: Title template string.
            untertitel: Subtitle template string.

        Returns:
            Dict with rendered 'titel' and 'untertitel'.
        """
        context = self._build_context()

        try:
            rendered_titel = Template(titel).render(context)
            rendered_untertitel = Template(untertitel).render(context)
        except Exception as e:
            return {
                'titel': f'[Fehler: {e}]',
                'untertitel': f'[Fehler: {e}]',
            }

        return {'titel': rendered_titel, 'untertitel': rendered_untertitel}

    def render_hero_preview(
        self,
        variant: str,
        title: str,
        subtitle: str,
        cta_text: str | None = None,
        cta_link: str | None = None,
        image_path: str | None = None
    ) -> str:
        """Render full hero section preview.

        Args:
            variant: Layout variant ('centered', 'split', 'overlay').
            title: Title text (may contain placeholders).
            subtitle: Subtitle text (may contain placeholders).
            cta_text: CTA button text.
            cta_link: CTA button link.
            image_path: Background image path.

        Returns:
            Rendered HTML string.
        """
        context = self._build_context()

        # Render text with placeholders
        rendered_title = self._render_text(title, context)
        rendered_subtitle = self._render_text(subtitle, context)

        # Create a mock hero object for template
        class MockHero:
            pass

        mock_hero = MockHero()
        mock_hero.variant = variant
        mock_hero.cta_text = cta_text
        mock_hero.cta_link = cta_link
        mock_hero.image_path = image_path

        template_path = f'hero/{variant}.html'

        try:
            from flask import render_template
            return render_template(
                template_path,
                hero=mock_hero,
                title=rendered_title,
                subtitle=rendered_subtitle,
            )
        except Exception:
            return self._render_fallback(mock_hero, rendered_title, rendered_subtitle)

    # ==============================================
    # Route-Based Hero Methods (NEW)
    # ==============================================

    def get_all_hero_sections(self) -> list[HeroSection]:
        """Get all hero sections (not just active).

        Returns:
            List of all HeroSection instances.
        """
        from v_flask_plugins.hero.models import HeroSection
        return HeroSection.query.order_by(
            HeroSection.active.desc(),
            HeroSection.name,
            HeroSection.id
        ).all()

    def get_hero_section(self, section_id: int) -> HeroSection | None:
        """Get a specific hero section by ID.

        Args:
            section_id: Hero section ID.

        Returns:
            HeroSection or None if not found.
        """
        from v_flask_plugins.hero.models import HeroSection
        return db.session.get(HeroSection, section_id)

    def get_hero_for_route(
        self,
        endpoint: str,
        slot: str = 'hero_top'
    ) -> HeroSection | None:
        """Find hero section assigned to a route and slot.

        Looks up the HeroAssignment table to find which hero section
        should be displayed for the given Flask endpoint and slot position.

        Args:
            endpoint: Flask endpoint name (e.g., 'public.index').
            slot: Slot position ('hero_top', 'above_content', 'below_content').

        Returns:
            HeroSection instance or None if no assignment found.
        """
        from v_flask_plugins.hero.models import (
            HeroAssignment,
            HeroSection,
            PageRoute,
        )

        # Find assignment for this endpoint and slot
        assignment = (
            db.session.query(HeroAssignment)
            .join(PageRoute)
            .join(HeroSection)
            .filter(
                PageRoute.endpoint == endpoint,
                HeroAssignment.slot_position == slot,
                HeroAssignment.active == True,  # noqa: E712
                HeroSection.active == True,  # noqa: E712
            )
            .order_by(HeroAssignment.priority.desc())
            .first()
        )

        if assignment:
            return assignment.hero_section

        return None

    def render_hero_slot(
        self,
        endpoint: str,
        slot: str = 'hero_top'
    ) -> str:
        """Render hero section for a specific endpoint and slot.

        Main method for frontend template integration. Call this from
        templates to render the assigned hero section.

        Args:
            endpoint: Flask endpoint name (e.g., 'public.index').
            slot: Slot position ('hero_top', 'above_content', 'below_content').

        Returns:
            Rendered HTML string, or empty string if no hero assigned.
        """
        hero = self.get_hero_for_route(endpoint, slot)

        if not hero:
            return ''

        return self.render_hero(hero)

    def get_assignments_for_hero(self, hero_id: int) -> list:
        """Get all page assignments for a hero section.

        Args:
            hero_id: Hero section ID.

        Returns:
            List of HeroAssignment instances.
        """
        from v_flask_plugins.hero.models import HeroAssignment
        return HeroAssignment.query.filter_by(
            hero_section_id=hero_id
        ).order_by(HeroAssignment.slot_position).all()

    def assign_hero_to_route(
        self,
        hero_id: int,
        route_id: int,
        slot: str = 'hero_top',
        priority: int = 100
    ) -> HeroAssignment | None:
        """Assign a hero section to a page route.

        Args:
            hero_id: Hero section ID.
            route_id: PageRoute ID.
            slot: Slot position.
            priority: Priority (higher wins conflicts).

        Returns:
            Created HeroAssignment or None on error.
        """
        from v_flask_plugins.hero.models import (
            HeroAssignment,
            HeroSection,
            PageRoute,
        )

        # Verify hero and route exist
        hero = db.session.get(HeroSection, hero_id)
        route = db.session.get(PageRoute, route_id)

        if not hero or not route:
            return None

        # Check if assignment already exists (unique constraint)
        existing = HeroAssignment.query.filter_by(
            page_route_id=route_id,
            slot_position=slot
        ).first()

        if existing:
            # Update existing assignment
            existing.hero_section_id = hero_id
            existing.priority = priority
            existing.active = True
        else:
            # Create new assignment
            existing = HeroAssignment(
                hero_section_id=hero_id,
                page_route_id=route_id,
                slot_position=slot,
                priority=priority,
            )
            db.session.add(existing)

        db.session.commit()
        return existing

    def remove_assignment(self, assignment_id: int) -> bool:
        """Remove a hero assignment.

        Args:
            assignment_id: HeroAssignment ID.

        Returns:
            True if removed, False if not found.
        """
        from v_flask_plugins.hero.models import HeroAssignment

        assignment = db.session.get(HeroAssignment, assignment_id)
        if assignment:
            db.session.delete(assignment)
            db.session.commit()
            return True
        return False


# Singleton instance for convenience
hero_service = HeroService()
