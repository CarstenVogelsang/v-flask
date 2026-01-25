"""Theme system for v-flask.

Themes provide base templates and CSS frameworks that define the visual
foundation of v-flask applications. They can be combined with plugins
via bundles.

Example:
    from v_flask.themes import ThemeManifest

    class MyTheme(ThemeManifest):
        name = 'my-theme'
        version = '1.0.0'
        description = 'Custom theme'
        css_framework = 'tailwind'
"""

from v_flask.themes.manifest import ThemeManifest
from v_flask.themes.registry import ThemeRegistry

__all__ = ['ThemeManifest', 'ThemeRegistry']
