"""Fragebogen Plugin Services."""

from v_flask_plugins.fragebogen.services.fragebogen_service import (
    FragebogenService,
    get_fragebogen_service,
    ValidationResult,
    EinladungResult,
    TeilnehmerResolver,
    DynamicTeilnehmerResolverAdapter,
)

from v_flask_plugins.fragebogen.services.participant_source import (
    DynamicParticipantResolver,
    get_dynamic_participant_resolver,
    reset_dynamic_participant_resolver,
    load_model_class,
    get_field_value,
    generate_greeting,
    ModelLoadError,
    FieldMappingError,
)

# Export service (optional dependency: openpyxl)
try:
    from v_flask_plugins.fragebogen.services.export_service import (
        FragebogenExportService,
        get_export_service,
        ExportOptions,
    )
    _EXPORT_AVAILABLE = True
except ImportError:
    # openpyxl not installed
    FragebogenExportService = None  # type: ignore
    get_export_service = None  # type: ignore
    ExportOptions = None  # type: ignore
    _EXPORT_AVAILABLE = False

__all__ = [
    # Core service
    'FragebogenService',
    'get_fragebogen_service',
    'ValidationResult',
    'EinladungResult',
    # Participant resolvers
    'TeilnehmerResolver',
    'DynamicTeilnehmerResolverAdapter',
    'DynamicParticipantResolver',
    'get_dynamic_participant_resolver',
    'reset_dynamic_participant_resolver',
    # Participant source helpers
    'load_model_class',
    'get_field_value',
    'generate_greeting',
    'ModelLoadError',
    'FieldMappingError',
    # Export service (optional)
    'FragebogenExportService',
    'get_export_service',
    'ExportOptions',
]
