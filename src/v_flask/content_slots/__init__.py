"""Content Slot System for v-flask.

This module provides a generic content slot system that allows plugins
to register content providers for specific page positions (slots).

Unlike UI-Slots (for menus, links), Content-Slots render dynamic HTML
content on pages. Examples: Hero sections, CTAs, banners, widgets.

Usage in plugins:
    from v_flask.content_slots import ContentSlotProvider, content_slot_registry

    class HeroSlotProvider(ContentSlotProvider):
        name = 'hero'
        priority = 100

        def render(self, endpoint: str, slot: str, context: dict) -> str | None:
            # Return HTML or None if nothing to render
            ...

    # In plugin's on_init():
    content_slot_registry.register(HeroSlotProvider())

Usage in templates:
    {{ render_content_slot('after_content', context={'ort': ort}) }}

Available slots:
    - top: Main hero/banner area at page top
    - before_content: Before main content
    - after_content: After main content (great for CTAs)
    - sidebar: Sidebar widgets
    - floating: Fixed-position floating elements
    - footer: Footer area content
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from flask import Flask


# Valid content slot positions
CONTENT_SLOTS = [
    'top',              # Main hero/banner area
    'before_content',   # Before main content
    'after_content',    # After main content (CTAs, related)
    'sidebar',          # Sidebar widgets
    'floating',         # Fixed-position elements
    'footer',           # Footer area content
]


class ContentSlotProvider(ABC):
    """Base class for content slot providers.

    Plugins create subclasses to provide content for specific slots.
    Multiple providers can register for the same slot - the one with
    highest priority that returns content wins.

    Attributes:
        name: Unique provider name (e.g., 'hero', 'cta').
        priority: Higher values = higher priority (default: 100).
        slots: List of slots this provider can handle.
    """

    name: str = 'unnamed'
    priority: int = 100
    slots: list[str] = []

    @abstractmethod
    def render(
        self,
        endpoint: str,
        slot: str,
        context: dict[str, Any],
    ) -> str | None:
        """Render content for a slot on a specific page.

        Args:
            endpoint: Flask endpoint name (e.g., 'public.index').
            slot: Slot position (e.g., 'after_content').
            context: Template context with additional data.

        Returns:
            HTML string to render, or None if this provider
            has nothing for this endpoint/slot combination.
        """
        pass

    def can_render(self, endpoint: str, slot: str) -> bool:
        """Check if this provider can potentially render for endpoint/slot.

        Override for more efficient filtering before calling render().
        Default implementation checks if slot is in self.slots.

        Args:
            endpoint: Flask endpoint name.
            slot: Slot position.

        Returns:
            True if this provider might have content for this slot.
        """
        if self.slots:
            return slot in self.slots
        return True


@dataclass
class ContentSlotRegistry:
    """Registry for content slot providers.

    Manages registration and rendering of content slot providers.
    Providers are sorted by priority (highest first) when rendering.

    Usage:
        registry = ContentSlotRegistry()
        registry.register(MyProvider())

        html = registry.render('public.index', 'after_content', {'key': 'val'})
    """

    _providers: list[ContentSlotProvider] = field(default_factory=list)

    def register(self, provider: ContentSlotProvider) -> None:
        """Register a content slot provider.

        Args:
            provider: ContentSlotProvider instance.

        Raises:
            ValueError: If provider with same name already registered.
        """
        # Check for duplicate names
        existing_names = [p.name for p in self._providers]
        if provider.name in existing_names:
            raise ValueError(
                f"Content slot provider '{provider.name}' already registered"
            )

        self._providers.append(provider)
        # Sort by priority (highest first)
        self._providers.sort(key=lambda p: p.priority, reverse=True)

    def unregister(self, provider_name: str) -> bool:
        """Unregister a provider by name.

        Args:
            provider_name: Name of the provider to remove.

        Returns:
            True if provider was found and removed, False otherwise.
        """
        for i, p in enumerate(self._providers):
            if p.name == provider_name:
                del self._providers[i]
                return True
        return False

    def render(
        self,
        endpoint: str,
        slot: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render content for a slot.

        Iterates through providers by priority until one returns content.

        Args:
            endpoint: Flask endpoint name.
            slot: Slot position to render.
            context: Additional context data for rendering.

        Returns:
            HTML string from the first provider that returns content,
            or empty string if no provider has content.
        """
        if slot not in CONTENT_SLOTS:
            return ''

        context = context or {}

        for provider in self._providers:
            # Quick check before full render
            if not provider.can_render(endpoint, slot):
                continue

            try:
                result = provider.render(endpoint, slot, context)
                if result:
                    return result
            except Exception:
                # Log error but continue to next provider
                continue

        return ''

    def get_providers(self, slot: str | None = None) -> list[ContentSlotProvider]:
        """Get all registered providers, optionally filtered by slot.

        Args:
            slot: Optional slot to filter by.

        Returns:
            List of providers, sorted by priority.
        """
        if slot is None:
            return list(self._providers)

        return [
            p for p in self._providers
            if not p.slots or slot in p.slots
        ]

    @property
    def provider_names(self) -> list[str]:
        """Get names of all registered providers."""
        return [p.name for p in self._providers]

    def __len__(self) -> int:
        return len(self._providers)


# Global registry instance
content_slot_registry = ContentSlotRegistry()


def create_context_processor(registry: ContentSlotRegistry) -> Callable:
    """Create a Flask context processor for content slot rendering.

    Args:
        registry: ContentSlotRegistry instance.

    Returns:
        Context processor function for Flask.

    Usage in VFlask.init_app():
        app.context_processor(create_context_processor(content_slot_registry))
    """
    def content_slot_context():
        from flask import request

        def render_content_slot(
            slot: str,
            context: dict[str, Any] | None = None,
        ) -> str:
            """Render a content slot for the current page.

            Args:
                slot: Slot position (e.g., 'after_content').
                context: Additional context for placeholders.

            Returns:
                Rendered HTML string or empty string.
            """
            # Get current endpoint
            endpoint = request.endpoint or ''

            return registry.render(endpoint, slot, context)

        def render_content_slot_for(
            endpoint: str,
            slot: str,
            context: dict[str, Any] | None = None,
        ) -> str:
            """Render a content slot for a specific endpoint.

            Use this when you need to render a slot for a different
            endpoint than the current page (e.g., in includes).

            Args:
                endpoint: Flask endpoint name.
                slot: Slot position.
                context: Additional context for placeholders.

            Returns:
                Rendered HTML string or empty string.
            """
            return registry.render(endpoint, slot, context)

        return {
            'render_content_slot': render_content_slot,
            'render_content_slot_for': render_content_slot_for,
            'CONTENT_SLOTS': CONTENT_SLOTS,
        }

    return content_slot_context


# Export public API
__all__ = [
    'CONTENT_SLOTS',
    'ContentSlotProvider',
    'ContentSlotRegistry',
    'content_slot_registry',
    'create_context_processor',
]
