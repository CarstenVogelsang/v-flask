"""Automatic service detection for the Datenschutz plugin.

Detects used services from:
1. Active v-flask plugins
2. Template content (scripts, embeds, etc.)

This helps users identify which privacy policy sections they need.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from flask import Flask


@dataclass
class DetectedService:
    """A detected service that may require privacy policy coverage.

    Attributes:
        baustein_id: The Baustein ID that covers this service
        source: How it was detected ('plugin' or 'template')
        details: Additional detection details (plugin name, file path, pattern)
    """

    baustein_id: str
    source: str  # 'plugin' or 'template'
    details: str


class DienstErkennung:
    """Automatic service detector for privacy policy coverage.

    Scans active plugins and templates to identify services that should be
    covered in the privacy policy.
    """

    def __init__(self, app: Flask):
        """Initialize detector with Flask app context.

        Args:
            app: The Flask application instance
        """
        self.app = app

    def detect_all(self) -> list[DetectedService]:
        """Detect all services from all sources.

        Returns:
            List of all detected services (deduplicated by baustein_id)
        """
        detected = []
        detected.extend(self.detect_from_plugins())
        detected.extend(self.detect_from_templates())

        # Deduplicate by baustein_id, keeping first occurrence
        seen = set()
        unique = []
        for service in detected:
            if service.baustein_id not in seen:
                seen.add(service.baustein_id)
                unique.append(service)

        return unique

    def detect_from_plugins(self) -> list[DetectedService]:
        """Detect services based on active v-flask plugins.

        Returns:
            List of detected services from plugins
        """
        detected = []

        # Mapping: Plugin name → list of Baustein IDs
        plugin_mapping = {
            'kontakt': ['kontaktformular'],
            'newsletter': ['newsletter'],
            'analytics': ['google_analytics', 'tracking_allgemein'],
            'comments': ['kommentare'],
            'auth': ['login'],
        }

        try:
            # Try to get active plugins from v-flask
            from v_flask.plugins import get_active_plugins

            active_plugins = get_active_plugins(self.app)
            for plugin in active_plugins:
                plugin_name = getattr(plugin, 'name', str(plugin))
                if plugin_name in plugin_mapping:
                    for baustein_id in plugin_mapping[plugin_name]:
                        detected.append(
                            DetectedService(
                                baustein_id=baustein_id,
                                source='plugin',
                                details=f'Plugin: {plugin_name}',
                            )
                        )
        except (ImportError, AttributeError):
            pass

        return detected

    def detect_from_templates(self) -> list[DetectedService]:
        """Detect services by scanning templates for known patterns.

        Scans all registered template folders for patterns like:
        - Google Analytics: gtag(, G-XXXXX
        - YouTube: youtube.com/embed
        - Google Maps: maps.googleapis.com
        - etc.

        Returns:
            List of detected services from template scanning
        """
        detected = []

        # Get all Bausteine with detection patterns
        from v_flask_plugins.datenschutz.bausteine import get_all_bausteine

        bausteine_with_patterns = [
            b for b in get_all_bausteine() if b.detect_patterns
        ]

        # Collect all template paths
        template_paths = self._get_template_paths()

        # Scan each template
        for template_path in template_paths:
            try:
                content = template_path.read_text(encoding='utf-8')

                for baustein in bausteine_with_patterns:
                    for pattern in baustein.detect_patterns:
                        if re.search(pattern, content):
                            detected.append(
                                DetectedService(
                                    baustein_id=baustein.id,
                                    source='template',
                                    details=f'Pattern "{pattern}" in {template_path.name}',
                                )
                            )
                            # Only need one match per Baustein per template
                            break

            except (UnicodeDecodeError, OSError):
                # Skip files that can't be read
                continue

        return detected

    def _get_template_paths(self) -> list[Path]:
        """Get all template file paths from the application.

        Returns:
            List of Path objects for all .html template files
        """
        template_paths = []

        # Get template folders from Flask app
        if self.app.template_folder:
            app_templates = Path(self.app.root_path) / self.app.template_folder
            if app_templates.exists():
                template_paths.extend(app_templates.rglob('*.html'))

        # Get template folders from blueprints
        for blueprint in self.app.blueprints.values():
            if blueprint.template_folder:
                bp_templates = Path(blueprint.root_path) / blueprint.template_folder
                if bp_templates.exists():
                    template_paths.extend(bp_templates.rglob('*.html'))

        # Get template folders from Jinja loader
        try:
            loader = self.app.jinja_env.loader
            if hasattr(loader, 'loaders'):
                # ChoiceLoader or similar
                for sub_loader in loader.loaders:
                    if hasattr(sub_loader, 'searchpath'):
                        for path in sub_loader.searchpath:
                            p = Path(path)
                            if p.exists():
                                template_paths.extend(p.rglob('*.html'))
        except Exception:
            pass

        # Deduplicate
        return list(set(template_paths))

    def get_unconfigured_services(
        self, aktivierte_bausteine: list[str]
    ) -> list[DetectedService]:
        """Get detected services that are not yet configured.

        Args:
            aktivierte_bausteine: List of already activated Baustein IDs

        Returns:
            List of detected services not in aktivierte_bausteine
        """
        all_detected = self.detect_all()
        return [s for s in all_detected if s.baustein_id not in aktivierte_bausteine]

    def get_detection_summary(self) -> dict:
        """Get a summary of all detected services grouped by source.

        Returns:
            Dict with 'plugins' and 'templates' keys containing lists of services
        """
        all_detected = self.detect_all()
        return {
            'plugins': [s for s in all_detected if s.source == 'plugin'],
            'templates': [s for s in all_detected if s.source == 'template'],
            'total': len(all_detected),
        }
