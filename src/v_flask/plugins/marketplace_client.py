"""Marketplace API client for fetching and downloading plugins.

This module provides the client-side integration with the V-Flask Marketplace,
allowing satellite projects to:
- Browse available plugins from the central marketplace
- Check their licenses
- Download licensed plugins
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import requests

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MarketplaceError(Exception):
    """Base exception for marketplace errors."""
    pass


class MarketplaceConnectionError(MarketplaceError):
    """Raised when unable to connect to the marketplace."""
    pass


class MarketplaceAuthError(MarketplaceError):
    """Raised when API key is invalid or missing."""
    pass


class PluginNotLicensedError(MarketplaceError):
    """Raised when trying to download a plugin without a license."""
    pass


class MarketplaceClient:
    """Client for the V-Flask Plugin Marketplace API.

    Usage:
        client = MarketplaceClient(
            base_url="https://marketplace.v-flask.de/api",
            api_key="vf_proj_xxxxx"
        )

        # Get available plugins (public, no auth required)
        plugins = client.get_available_plugins()

        # Get project's licenses (requires auth)
        licenses = client.get_my_licenses()

        # Download a plugin (requires auth + license)
        zip_content = client.download_plugin('kontakt')
    """

    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """Initialize the marketplace client.

        Args:
            base_url: Base URL of the marketplace API.
                      Can also be set via VFLASK_MARKETPLACE_URL config.
            api_key: Project API key for authentication.
                     Can also be set via VFLASK_PROJECT_API_KEY config.
            timeout: Request timeout in seconds.
        """
        self._base_url = base_url
        self._api_key = api_key
        self._timeout = timeout
        self._plugins_cache: list[dict] | None = None
        self._licenses_cache: list[dict] | None = None

    @property
    def base_url(self) -> str | None:
        """Get the marketplace base URL."""
        if self._base_url:
            return self._base_url

        # Try to get from Flask config
        try:
            from flask import current_app
            return current_app.config.get('VFLASK_MARKETPLACE_URL')
        except RuntimeError:
            return None

    @property
    def api_key(self) -> str | None:
        """Get the API key."""
        if self._api_key:
            return self._api_key

        # Try to get from Flask config
        try:
            from flask import current_app
            return current_app.config.get('VFLASK_PROJECT_API_KEY')
        except RuntimeError:
            return None

    @property
    def is_configured(self) -> bool:
        """Check if the marketplace client is configured."""
        return bool(self.base_url)

    def _get_headers(self, auth_required: bool = False) -> dict[str, str]:
        """Get headers for API requests.

        Args:
            auth_required: Whether authentication is required.

        Returns:
            Headers dictionary.

        Raises:
            MarketplaceAuthError: If auth is required but no API key.
        """
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'v-flask-client/1.0',
        }

        if auth_required:
            if not self.api_key:
                raise MarketplaceAuthError(
                    "API-Key erforderlich. Setze VFLASK_PROJECT_API_KEY in der Konfiguration."
                )
            headers['X-API-Key'] = self.api_key

        return headers

    def _make_request(
        self,
        method: str,
        endpoint: str,
        auth_required: bool = False,
        **kwargs: Any,
    ) -> requests.Response:
        """Make an HTTP request to the marketplace API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/plugins')
            auth_required: Whether authentication is required.
            **kwargs: Additional arguments for requests.

        Returns:
            Response object.

        Raises:
            MarketplaceConnectionError: If unable to connect.
            MarketplaceAuthError: If authentication fails.
        """
        if not self.base_url:
            raise MarketplaceConnectionError(
                "Marketplace nicht konfiguriert. Setze VFLASK_MARKETPLACE_URL."
            )

        url = urljoin(self.base_url.rstrip('/') + '/', endpoint.lstrip('/'))
        headers = self._get_headers(auth_required)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self._timeout,
                **kwargs,
            )

            if response.status_code == 401:
                raise MarketplaceAuthError("Ungültiger API-Key.")

            if response.status_code == 403:
                raise MarketplaceAuthError("Zugriff verweigert.")

            return response

        except requests.ConnectionError as e:
            raise MarketplaceConnectionError(
                f"Verbindung zum Marketplace fehlgeschlagen: {e}"
            ) from e
        except requests.Timeout as e:
            raise MarketplaceConnectionError(
                f"Marketplace-Anfrage Timeout: {e}"
            ) from e

    def get_available_plugins(self, force_refresh: bool = False) -> list[dict]:
        """Get list of available plugins from the marketplace.

        This endpoint is public but optionally accepts API key authentication.
        When authenticated with a superadmin project's API key, alpha/beta
        plugins are also returned.

        Results are cached until force_refresh is True.

        Args:
            force_refresh: Force refresh of cached data.

        Returns:
            List of plugin metadata dictionaries.
        """
        if self._plugins_cache is not None and not force_refresh:
            return self._plugins_cache

        if not self.is_configured:
            logger.debug("Marketplace not configured, returning empty list")
            return []

        try:
            # Send API key if available (allows seeing alpha/beta plugins for superadmin projects)
            params = {}
            if self.api_key:
                params['api_key'] = self.api_key

            response = self._make_request('GET', '/plugins', params=params)
            response.raise_for_status()

            data = response.json()
            self._plugins_cache = data.get('plugins', [])
            return self._plugins_cache

        except MarketplaceError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch plugins: {e}")
            return []

    def get_plugin_info(self, name: str) -> dict | None:
        """Get plugin info by name.

        Args:
            name: Plugin name.

        Returns:
            Plugin metadata or None if not found.
        """
        for plugin in self.get_available_plugins():
            if plugin.get('name') == name:
                return plugin
        return None

    def get_my_licenses(self, force_refresh: bool = False) -> list[dict]:
        """Get licenses for the current project.

        Requires authentication via API key.

        Args:
            force_refresh: Force refresh of cached data.

        Returns:
            List of license dictionaries.
        """
        if self._licenses_cache is not None and not force_refresh:
            return self._licenses_cache

        if not self.is_configured:
            return []

        try:
            response = self._make_request(
                'GET',
                '/projects/me/licenses',
                auth_required=True,
            )
            response.raise_for_status()

            data = response.json()
            self._licenses_cache = data.get('licenses', [])
            return self._licenses_cache

        except MarketplaceAuthError:
            raise
        except MarketplaceError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch licenses: {e}")
            return []

    def get_licensed_plugin_names(self) -> set[str]:
        """Get set of plugin names that are licensed.

        Returns:
            Set of licensed plugin names.
        """
        licenses = self.get_my_licenses()
        return {lic.get('plugin_name') for lic in licenses if lic.get('is_active')}

    def is_plugin_licensed(self, name: str) -> bool:
        """Check if a plugin is licensed for this project.

        Args:
            name: Plugin name.

        Returns:
            True if plugin is licensed.
        """
        return name in self.get_licensed_plugin_names()

    def is_plugin_free(self, name: str) -> bool:
        """Check if a plugin is free (no license required).

        Args:
            name: Plugin name.

        Returns:
            True if plugin is free.
        """
        info = self.get_plugin_info(name)
        if not info:
            return False
        return info.get('is_free', False) or info.get('price_cents', 0) == 0

    def can_download_plugin(self, name: str) -> bool:
        """Check if a plugin can be downloaded.

        A plugin can be downloaded if:
        - It's free, OR
        - The project has a valid license

        Args:
            name: Plugin name.

        Returns:
            True if plugin can be downloaded.
        """
        if self.is_plugin_free(name):
            return True
        return self.is_plugin_licensed(name)

    def download_plugin(self, name: str) -> bytes:
        """Download a plugin ZIP archive.

        Requires authentication and appropriate license.

        Args:
            name: Plugin name to download.

        Returns:
            ZIP file content as bytes.

        Raises:
            PluginNotLicensedError: If plugin is not licensed.
            MarketplaceError: On other errors.
        """
        if not self.can_download_plugin(name):
            raise PluginNotLicensedError(
                f"Plugin '{name}' ist nicht lizenziert für dieses Projekt."
            )

        response = self._make_request(
            'POST',
            f'/plugins/{name}/download',
            auth_required=True,
        )

        if response.status_code == 403:
            raise PluginNotLicensedError(
                f"Plugin '{name}' ist nicht lizenziert für dieses Projekt."
            )

        if response.status_code == 404:
            raise MarketplaceError(f"Plugin '{name}' nicht gefunden.")

        response.raise_for_status()
        return response.content

    def get_project_info(self) -> dict | None:
        """Get information about the current project.

        Returns:
            Project info dictionary or None.
        """
        try:
            response = self._make_request(
                'GET',
                '/projects/me',
                auth_required=True,
            )
            response.raise_for_status()
            return response.json().get('project')
        except Exception as e:
            logger.error(f"Failed to fetch project info: {e}")
            return None

    def get_plugin_categories(self) -> list[dict]:
        """Get list of plugin categories from the marketplace.

        Returns:
            List of category dictionaries with code, name_de, icon, color_hex.
        """
        if not self.is_configured:
            return []

        try:
            response = self._make_request('GET', '/plugin-categories')
            response.raise_for_status()
            return response.json().get('categories', [])
        except Exception as e:
            logger.debug(f"Failed to fetch categories: {e}")
            return []

    def refresh_cache(self) -> None:
        """Clear all cached data."""
        self._plugins_cache = None
        self._licenses_cache = None


# Singleton instance (configured via Flask app)
_client_instance: MarketplaceClient | None = None


def get_marketplace_client() -> MarketplaceClient:
    """Get the marketplace client instance.

    Returns a singleton instance that reads configuration from Flask app.

    Returns:
        MarketplaceClient instance.
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = MarketplaceClient()
    return _client_instance


def init_marketplace_client(app) -> None:
    """Initialize the marketplace client with app configuration.

    Call this during app initialization to configure the client.

    Args:
        app: Flask application instance.
    """
    global _client_instance
    _client_instance = MarketplaceClient(
        base_url=app.config.get('VFLASK_MARKETPLACE_URL'),
        api_key=app.config.get('VFLASK_PROJECT_API_KEY'),
    )
