"""Local cache for plugin metadata from Marketplace.

This module provides caching for plugin metadata fetched from the Marketplace API.
When the Marketplace is unreachable, cached data is used as a fallback for
installed plugins only.

Non-installed plugins (marketplace-only) are NOT cached and will not appear
when the Marketplace is offline.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class PluginMetaCache:
    """Cache for plugin metadata fetched from Marketplace.

    Only caches metadata for INSTALLED plugins.
    Cache is stored in instance/plugin_meta_cache.json

    Cached fields per plugin:
    - icon: Tabler icon class (e.g., "ti ti-mail")
    - categories: List of category codes
    - category_info: Full category data (code, name_de, icon, color_hex)
    - phase_badge: Phase badge data (label, color)
    - cached_at: ISO timestamp of when data was cached

    Usage:
        cache = PluginMetaCache(Path(app.instance_path))

        # Get cached data
        meta = cache.get('kontakt')

        # Update single plugin
        cache.update('kontakt', {'icon': 'ti ti-mail', ...})

        # Update multiple plugins at once
        cache.update_batch([{'name': 'kontakt', 'icon': 'ti ti-mail', ...}])
    """

    CACHE_FILENAME = 'plugin_meta_cache.json'

    def __init__(self, instance_path: Path):
        """Initialize the cache.

        Args:
            instance_path: Path to Flask instance folder.
        """
        self.cache_file = instance_path / self.CACHE_FILENAME
        self._cache: dict[str, dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, encoding='utf-8') as f:
                    self._cache = json.load(f)
                logger.debug(f"Loaded plugin cache with {len(self._cache)} entries")
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse plugin cache (invalid JSON): {e}")
                self._cache = {}
            except Exception as e:
                logger.warning(f"Could not load plugin cache: {e}")
                self._cache = {}
        else:
            logger.debug("No plugin cache file found, starting with empty cache")
            self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"Saved plugin cache with {len(self._cache)} entries")
        except Exception as e:
            logger.error(f"Could not save plugin cache: {e}")

    def get(self, plugin_name: str) -> dict[str, Any] | None:
        """Get cached metadata for a plugin.

        Args:
            plugin_name: Plugin name (e.g., 'kontakt').

        Returns:
            Cached metadata dict or None if not cached.
        """
        return self._cache.get(plugin_name)

    def update(self, plugin_name: str, metadata: dict[str, Any]) -> None:
        """Update cache for a single plugin.

        Args:
            plugin_name: Plugin name.
            metadata: Metadata dict with icon, categories, category_info, phase_badge.
        """
        self._cache[plugin_name] = {
            'icon': metadata.get('icon'),
            'categories': metadata.get('categories'),
            'category_info': metadata.get('category_info'),
            'phase_badge': metadata.get('phase_badge'),
            'cached_at': datetime.now(timezone.utc).isoformat(),
        }
        self._save_cache()

    def update_batch(self, plugins: list[dict[str, Any]]) -> None:
        """Update cache for multiple plugins at once.

        More efficient than calling update() multiple times
        as it only writes to disk once.

        Args:
            plugins: List of plugin dicts with 'name' key and metadata.
        """
        now = datetime.now(timezone.utc).isoformat()
        updated = 0

        for plugin in plugins:
            name = plugin.get('name')
            if name:
                self._cache[name] = {
                    'icon': plugin.get('icon'),
                    'categories': plugin.get('categories'),
                    'category_info': plugin.get('category_info'),
                    'phase_badge': plugin.get('phase_badge'),
                    'cached_at': now,
                }
                updated += 1

        if updated > 0:
            self._save_cache()
            logger.debug(f"Updated cache for {updated} plugins")

    def remove(self, plugin_name: str) -> bool:
        """Remove a plugin from cache.

        Args:
            plugin_name: Plugin name to remove.

        Returns:
            True if plugin was in cache, False otherwise.
        """
        if plugin_name in self._cache:
            del self._cache[plugin_name]
            self._save_cache()
            return True
        return False

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache = {}
        self._save_cache()
        logger.info("Plugin cache cleared")

    def get_all(self) -> dict[str, dict[str, Any]]:
        """Get all cached plugin metadata.

        Returns:
            Dict mapping plugin names to their cached metadata.
        """
        return self._cache.copy()

    @property
    def cache_age_info(self) -> dict[str, str]:
        """Get cache age information for each plugin.

        Returns:
            Dict mapping plugin names to their cached_at timestamps.
        """
        return {
            name: data.get('cached_at', 'unknown')
            for name, data in self._cache.items()
        }
