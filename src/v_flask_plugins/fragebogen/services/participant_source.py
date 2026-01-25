"""Dynamic Participant Source Service.

Provides TeilnehmerResolver implementation that loads participant data
from configurable models using ParticipantSourceConfig.

This enables host applications to configure which models (Kunde, Lead,
Unternehmen, etc.) should be used as participant data sources without
modifying plugin code.

Example:
    # Configure a participant source via admin UI or directly:
    config = ParticipantSourceConfig(
        model_path='myapp.models.Kunde',
        display_name='Kunden',
        field_mapping={
            'email': 'email',
            'name': {'fields': ['vorname', 'nachname'], 'separator': ' '},
            'anrede': 'anrede',
            'titel': 'titel'
        },
        greeting_template='{{ anrede }} {{ titel }} {{ name }}'
    )

    # The resolver automatically uses the config:
    resolver = get_dynamic_participant_resolver()
    email = resolver.get_email(kunde_id, 'kunde')
    greeting = resolver.get_greeting(kunde_id, 'kunde')
"""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, BaseLoader

if TYPE_CHECKING:
    from v_flask_plugins.fragebogen.models import ParticipantSourceConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================

class ModelLoadError(Exception):
    """Raised when a model cannot be loaded from its import path."""
    pass


class FieldMappingError(Exception):
    """Raised when field mapping fails."""
    pass


# =============================================================================
# Helper Functions
# =============================================================================

def load_model_class(model_path: str):
    """Dynamically load a model class from its import path.

    Args:
        model_path: Full import path (e.g., 'myapp.models.Kunde').

    Returns:
        The model class.

    Raises:
        ModelLoadError: If the model cannot be loaded.
    """
    try:
        module_path, class_name = model_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError, ValueError) as e:
        raise ModelLoadError(f"Cannot load model '{model_path}': {e}")


def get_field_value(instance: Any, field_spec: str | dict) -> str | None:
    """Extract field value from a model instance using the field specification.

    Args:
        instance: The model instance.
        field_spec: Either a string (single field) or dict (composite field).
            Single field: "email"
            Composite: {"fields": ["vorname", "nachname"], "separator": " "}

    Returns:
        The extracted value as string, or None.

    Example:
        # Single field
        email = get_field_value(kunde, "email")  # -> "test@example.com"

        # Composite field
        name = get_field_value(kunde, {
            "fields": ["vorname", "nachname"],
            "separator": " "
        })  # -> "Max Mustermann"
    """
    if instance is None:
        return None

    if isinstance(field_spec, str):
        # Simple field access
        value = getattr(instance, field_spec, None)
        return str(value) if value is not None else None

    if isinstance(field_spec, dict):
        # Composite field
        fields = field_spec.get('fields', [])
        separator = field_spec.get('separator', ' ')

        values = []
        for field in fields:
            value = getattr(instance, field, None)
            if value:
                values.append(str(value))

        return separator.join(values) if values else None

    return None


# =============================================================================
# DynamicParticipantResolver
# =============================================================================

class DynamicParticipantResolver:
    """TeilnehmerResolver that uses ParticipantSourceConfig for field mapping.

    This resolver dynamically loads participant data from configurable models,
    supporting:
    - Single field mapping (email -> email)
    - Composite field mapping (name -> vorname + nachname)
    - Optional greeting templates with Jinja2
    - Prefill value support for any model field

    The resolver implements caching for both config and model lookups to
    minimize database queries and import overhead.
    """

    def __init__(self):
        """Initialize the resolver with empty caches."""
        self._config_cache: dict[str, ParticipantSourceConfig | None] = {}
        self._model_cache: dict[str, type] = {}
        self._jinja_env = Environment(loader=BaseLoader())

    # =========================================================================
    # Cache Management
    # =========================================================================

    def clear_cache(self) -> None:
        """Clear all caches.

        Call this after config changes to ensure fresh data is loaded.
        """
        self._config_cache.clear()
        self._model_cache.clear()

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _get_config(self, teilnehmer_typ: str) -> 'ParticipantSourceConfig | None':
        """Get cached config for a participant type."""
        if teilnehmer_typ not in self._config_cache:
            from v_flask_plugins.fragebogen.models import ParticipantSourceConfig
            config = ParticipantSourceConfig.get_for_type(teilnehmer_typ)
            self._config_cache[teilnehmer_typ] = config

        return self._config_cache.get(teilnehmer_typ)

    def _get_model_class(self, model_path: str):
        """Get cached model class."""
        if model_path not in self._model_cache:
            self._model_cache[model_path] = load_model_class(model_path)
        return self._model_cache[model_path]

    def _get_instance(self, teilnehmer_id: int, teilnehmer_typ: str) -> Any | None:
        """Load a participant instance from the database.

        Args:
            teilnehmer_id: The participant's primary key.
            teilnehmer_typ: The participant type (used to find config).

        Returns:
            The model instance or None if not found.
        """
        config = self._get_config(teilnehmer_typ)
        if not config:
            logger.warning(f"No config for participant type: {teilnehmer_typ}")
            return None

        try:
            model_class = self._get_model_class(config.model_path)
            from v_flask.extensions import db
            return db.session.get(model_class, teilnehmer_id)
        except ModelLoadError as e:
            logger.error(str(e))
            return None

    # =========================================================================
    # TeilnehmerResolver Interface
    # =========================================================================

    def get_email(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        """Get email address for a participant.

        Args:
            teilnehmer_id: The participant's primary key.
            teilnehmer_typ: The participant type.

        Returns:
            Email address or None if not found.
        """
        config = self._get_config(teilnehmer_typ)
        if not config:
            return None

        instance = self._get_instance(teilnehmer_id, teilnehmer_typ)
        if not instance:
            return None

        email_spec = config.field_mapping.get('email')
        if not email_spec:
            logger.warning(f"No email mapping in config: {config.display_name}")
            return None

        return get_field_value(instance, email_spec)

    def get_name(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        """Get display name for a participant.

        Args:
            teilnehmer_id: The participant's primary key.
            teilnehmer_typ: The participant type.

        Returns:
            Display name or None if not found.
        """
        config = self._get_config(teilnehmer_typ)
        if not config:
            return None

        instance = self._get_instance(teilnehmer_id, teilnehmer_typ)
        if not instance:
            return None

        name_spec = config.field_mapping.get('name')
        if not name_spec:
            return None

        return get_field_value(instance, name_spec)

    def get_anrede(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        """Get salutation (Anrede) for a participant.

        Args:
            teilnehmer_id: The participant's primary key.
            teilnehmer_typ: The participant type.

        Returns:
            Anrede (Herr/Frau/Divers) or None.
        """
        config = self._get_config(teilnehmer_typ)
        if not config:
            return None

        instance = self._get_instance(teilnehmer_id, teilnehmer_typ)
        if not instance:
            return None

        anrede_spec = config.field_mapping.get('anrede')
        if not anrede_spec:
            return None

        return get_field_value(instance, anrede_spec)

    def get_titel(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        """Get title (Dr., Prof.) for a participant.

        Args:
            teilnehmer_id: The participant's primary key.
            teilnehmer_typ: The participant type.

        Returns:
            Title or None.
        """
        config = self._get_config(teilnehmer_typ)
        if not config:
            return None

        instance = self._get_instance(teilnehmer_id, teilnehmer_typ)
        if not instance:
            return None

        titel_spec = config.field_mapping.get('titel')
        if not titel_spec:
            return None

        return get_field_value(instance, titel_spec)

    def get_greeting(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        """Get personalized greeting using template.

        Uses the greeting_template from ParticipantSourceConfig to generate
        a personalized greeting. Available template variables:
        - name: Participant name
        - email: Participant email
        - anrede: Salutation (Herr/Frau/Divers)
        - titel: Title (Dr., Prof.)

        Example template:
            "Sehr geehrte{{ 'r' if anrede == 'Herr' else '' }} {{ anrede }} {{ titel }} {{ name }}"

        Args:
            teilnehmer_id: The participant's primary key.
            teilnehmer_typ: The participant type.

        Returns:
            Formatted greeting string or None if no template configured.
        """
        config = self._get_config(teilnehmer_typ)
        if not config or not config.greeting_template:
            return None

        # Build context for template
        context = {
            'name': self.get_name(teilnehmer_id, teilnehmer_typ) or '',
            'email': self.get_email(teilnehmer_id, teilnehmer_typ) or '',
            'anrede': self.get_anrede(teilnehmer_id, teilnehmer_typ) or '',
            'titel': self.get_titel(teilnehmer_id, teilnehmer_typ) or '',
        }

        try:
            template = self._jinja_env.from_string(config.greeting_template)
            return template.render(**context).strip()
        except Exception as e:
            logger.error(f"Error rendering greeting template: {e}")
            return None

    def get_prefill_value(
        self,
        teilnehmer_id: int,
        teilnehmer_typ: str,
        prefill_key: str
    ) -> Any | None:
        """Get prefill value for a field.

        Supports prefill keys in the format:
        - "teilnehmer.<field>" - Maps to model field via generic prefix
        - "<typ>.<field>" - Type-specific field access (e.g., "kunde.firmierung")

        Args:
            teilnehmer_id: Participant ID.
            teilnehmer_typ: Participant type.
            prefill_key: The prefill key from question definition.

        Returns:
            The prefill value or None.
        """
        config = self._get_config(teilnehmer_typ)
        if not config:
            return None

        instance = self._get_instance(teilnehmer_id, teilnehmer_typ)
        if not instance:
            return None

        # Parse prefill key
        # Format: "teilnehmer.email" or "kunde.firmierung"
        parts = prefill_key.split('.', 1)
        if len(parts) != 2:
            return None

        prefix, field_name = parts

        # Check if prefix matches (generic "teilnehmer" or specific type)
        type_id = config.get_type_identifier()
        if prefix not in ('teilnehmer', type_id):
            return None

        # First check field_mapping for special mappings
        if field_name in config.field_mapping:
            return get_field_value(instance, config.field_mapping[field_name])

        # Otherwise try direct attribute access
        return getattr(instance, field_name, None)


# =============================================================================
# Greeting Generator (Standalone Function)
# =============================================================================

def generate_greeting(
    anrede: str | None,
    titel: str | None,
    name: str | None,
    template: str | None = None
) -> str:
    """Generate a personalized greeting from components.

    This is a standalone function for cases where you have the individual
    components already and don't need to load from a model.

    Args:
        anrede: Salutation (Herr/Frau/Divers).
        titel: Title (Dr., Prof.).
        name: Full name.
        template: Optional Jinja2 template. If not provided, uses default.

    Returns:
        Formatted greeting string.

    Example:
        greeting = generate_greeting('Herr', 'Dr.', 'Müller')
        # -> "Sehr geehrter Herr Dr. Müller"
    """
    # Filter out None/empty values
    anrede = anrede or ''
    titel = titel or ''
    name = name or ''

    if template:
        try:
            env = Environment(loader=BaseLoader())
            jinja_template = env.from_string(template)
            return jinja_template.render(
                anrede=anrede,
                titel=titel,
                name=name
            ).strip()
        except Exception as e:
            logger.warning(f"Greeting template error: {e}")

    # Default greeting format
    parts = []

    if anrede:
        # Determine "Sehr geehrter/geehrte"
        if anrede.lower() == 'herr':
            parts.append('Sehr geehrter Herr')
        elif anrede.lower() == 'frau':
            parts.append('Sehr geehrte Frau')
        else:
            parts.append(f'Guten Tag {anrede}')

        if titel:
            parts.append(titel)
        if name:
            parts.append(name)
    elif name:
        # No anrede, just use name
        parts.append(f'Guten Tag {name}')
    else:
        # Fallback
        return 'Guten Tag'

    return ' '.join(parts)


# =============================================================================
# Singleton
# =============================================================================

_dynamic_resolver: DynamicParticipantResolver | None = None


def get_dynamic_participant_resolver() -> DynamicParticipantResolver:
    """Get the dynamic participant resolver singleton.

    Returns:
        The shared DynamicParticipantResolver instance.
    """
    global _dynamic_resolver
    if _dynamic_resolver is None:
        _dynamic_resolver = DynamicParticipantResolver()
    return _dynamic_resolver


def reset_dynamic_participant_resolver() -> None:
    """Reset the singleton (clears cache).

    Call this after ParticipantSourceConfig changes.
    """
    global _dynamic_resolver
    if _dynamic_resolver is not None:
        _dynamic_resolver.clear_cache()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'DynamicParticipantResolver',
    'get_dynamic_participant_resolver',
    'reset_dynamic_participant_resolver',
    'load_model_class',
    'get_field_value',
    'generate_greeting',
    'ModelLoadError',
    'FieldMappingError',
]
