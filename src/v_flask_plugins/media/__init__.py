"""VFlask Media Library Plugin.

A comprehensive media management plugin with:
- File upload with automatic resizing
- Pexels & Unsplash stock photo integration
- Media picker component for other plugins
- Categorization and search

Usage:
    from v_flask import VFlask
    from v_flask_plugins.media import MediaPlugin

    v_flask = VFlask()
    v_flask.register_plugin(MediaPlugin())
    v_flask.init_app(app)

In templates:
    {{ get_media_picker_html('field_name', current_media_id) }}
    {{ get_media_url(media_id, size='medium') }}

Configuration:
    UPLOAD_FOLDER: Storage location (default: instance/media)
    PEXELS_API_KEY: Pexels API key (optional)
    UNSPLASH_ACCESS_KEY: Unsplash access key (optional)
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class MediaPlugin(PluginManifest):
    """Media Library plugin for v-flask applications.

    Provides:
        - File upload with validation and automatic resizing
        - Stock photo integration (Pexels, Unsplash)
        - Media picker component for embedding in other plugins
        - Admin interface for library management
    """

    name = 'media'
    version = '1.0.0'
    description = 'Zentrale Media-Library mit Stock-Photo Integration (Pexels, Unsplash)'
    author = 'v-flask'

    # No dependencies on other plugins
    dependencies = []

    # Marketplace metadata
    long_description = '''
Ein umfassendes Media-Management Plugin für v-flask.

**Features:**
- Datei-Upload mit automatischem Resizing (thumbnail, small, medium, large)
- Pexels Stock-Photo Integration
- Unsplash Stock-Photo Integration
- Media Picker Komponente für andere Plugins
- Kategorisierung und Tagging
- SEO-Metadaten (alt_text, title, caption)
- Suche nach Dateiname, Titel, Alt-Text

**Resize-Presets:**
- thumbnail: 150x150px
- small: 400x400px
- medium: 800x800px
- large: 1200x1200px

**Konfiguration:**
```env
UPLOAD_FOLDER=instance/media
PEXELS_API_KEY=xxx          # Optional
UNSPLASH_ACCESS_KEY=xxx     # Optional
```

**Verwendung in Templates:**
```jinja2
{{ get_media_picker_html('image_id', entity.media_id) }}
{{ get_media_url(media_id, size='medium') }}
```
'''
    license = 'MIT'
    categories = ['content', 'media']
    tags = ['media', 'images', 'upload', 'pexels', 'unsplash', 'stock-photos', 'resize']
    min_v_flask_version = '0.2.0'

    # Admin navigation: appears under "Inhalte" category
    admin_category = 'content'

    # UI Slots: Automatic UI integration when plugin is activated
    ui_slots = {
        'admin_menu': [
            {
                'label': 'Medienbibliothek',
                'url': 'media_admin.library',
                'icon': 'ti ti-photo',
                'permission': 'admin.*',
                'order': 10,
            }
        ],
    }

    def get_models(self):
        """Return the Media model."""
        from v_flask_plugins.media.models import Media
        return [Media]

    def get_blueprints(self):
        """Return admin blueprint for media management."""
        from v_flask_plugins.media.routes import media_admin_bp
        return [
            (media_admin_bp, '/admin/media'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def get_settings_schema(self) -> list[dict]:
        """Define available settings for the Media plugin.

        Returns:
            List of setting definitions for Pexels/Unsplash API keys
            and upload configuration.
        """
        return [
            {
                'key': 'pexels_api_key',
                'label': 'Pexels API Key',
                'type': 'password',
                'description': 'API Key von pexels.com/api - Ermöglicht Stock-Foto-Suche',
                'required': False,
            },
            {
                'key': 'unsplash_access_key',
                'label': 'Unsplash Access Key',
                'type': 'password',
                'description': 'Access Key von unsplash.com/developers - Ermöglicht Stock-Foto-Suche',
                'required': False,
            },
            {
                'key': 'max_upload_size_mb',
                'label': 'Max. Upload-Größe (MB)',
                'type': 'int',
                'description': 'Maximale Dateigröße für Uploads in Megabyte',
                'default': 10,
                'min': 1,
                'max': 50,
            },
            {
                'key': 'auto_resize',
                'label': 'Automatisches Resizing',
                'type': 'bool',
                'description': 'Bilder automatisch in verschiedene Größen konvertieren',
                'default': True,
            },
        ]

    def on_settings_saved(self, settings: dict) -> None:
        """Clear cached API clients when settings change.

        Args:
            settings: Dictionary of saved settings.
        """
        # Clear cached clients so they're recreated with new keys
        try:
            from v_flask_plugins.media.services import pexels_service, unsplash_service
            pexels_service._client = None
            unsplash_service._client = None
        except (ImportError, AttributeError):
            pass

    def on_init(self, app):
        """Register context processors and public media route."""
        from flask import send_from_directory
        from v_flask_plugins.media.services.media_service import media_service

        # Register public media route for serving files
        @app.route('/media/<path:filename>')
        def serve_media(filename):
            """Serve media files from upload folder.

            Note: In production, configure your web server (nginx/caddy)
            to serve /media/ directly from UPLOAD_FOLDER for better performance.
            """
            upload_folder = app.config.get('UPLOAD_FOLDER', 'instance/media')
            return send_from_directory(upload_folder, filename)

        # Register context processor for template helpers
        @app.context_processor
        def media_context():
            """Provide media helper functions to templates."""

            def get_media_picker_html(
                field_name: str = 'media_id',
                current_media_id: int | None = None,
                accept: str = 'image/*'
            ) -> str:
                """Render Media Picker Component.

                Args:
                    field_name: Name of the hidden input field.
                    current_media_id: Currently selected media ID.
                    accept: MIME type filter (e.g., 'image/*').

                Returns:
                    HTML string for the media picker component.

                Usage:
                    {{ get_media_picker_html('hero_image_id', hero.media_id) }}
                """
                return media_service.render_picker_component(
                    field_name=field_name,
                    current_media_id=current_media_id,
                    accept=accept
                )

            def get_media_url(media_id: int | None, size: str = 'medium') -> str:
                """Get URL for media file with optional size variant.

                Args:
                    media_id: Media ID to get URL for.
                    size: Size variant (thumbnail, small, medium, large, original).

                Returns:
                    URL string or empty string if media not found.

                Usage:
                    <img src="{{ get_media_url(entity.media_id, 'thumbnail') }}">
                """
                return media_service.get_url(media_id, size)

            def get_media(media_id: int | None):
                """Get Media instance by ID.

                Args:
                    media_id: Media ID to retrieve.

                Returns:
                    Media instance or None.

                Usage:
                    {% set media = get_media(entity.media_id) %}
                    {% if media %}{{ media.attribution_html|safe }}{% endif %}
                """
                return media_service.get_media(media_id)

            return {
                'get_media_picker_html': get_media_picker_html,
                'get_media_url': get_media_url,
                'get_media': get_media,
            }


# Export the plugin class
__all__ = ['MediaPlugin']
