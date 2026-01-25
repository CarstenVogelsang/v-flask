"""Bundle system for v-flask.

Bundles combine themes with plugin sets to create complete starter kits.
A bundle provides a preconfigured combination of visual design (theme)
and functionality (plugins) that can be activated with a single call.

Example:
    from v_flask.bundles import BundleManifest
    from v_flask.themes import ThemeManifest

    class MFRBundle(BundleManifest):
        name = 'mfr'
        version = '1.0.0'
        description = 'Manufacturer B2B Portal'
        theme = MFRTailwindTheme
        required_plugins = ['crm']

    # In app factory:
    v_flask = VFlask()
    v_flask.use_bundle('mfr')
    v_flask.init_app(app)
"""

from v_flask.bundles.manifest import BundleManifest
from v_flask.bundles.registry import BundleRegistry

__all__ = ['BundleManifest', 'BundleRegistry']
