"""OpenAPI spec fetching and parsing service.

Handles:
    - Fetching OpenAPI specs from URLs (JSON and YAML)
    - Caching specs in the database
    - Extracting endpoints and schemas
"""

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from v_flask_plugins.api_market.models import ExternalApi

logger = logging.getLogger(__name__)


class OpenAPIFetchError(Exception):
    """Raised when fetching OpenAPI spec fails."""
    pass


def fetch_openapi_spec(url: str, timeout: int = 30) -> dict:
    """Fetch and parse an OpenAPI spec from a URL.

    Args:
        url: URL to the OpenAPI spec (JSON or YAML).
        timeout: Request timeout in seconds.

    Returns:
        Parsed OpenAPI spec as dictionary.

    Raises:
        OpenAPIFetchError: If fetching or parsing fails.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')

        # Try JSON first
        if 'json' in content_type or url.endswith('.json'):
            return response.json()

        # Try YAML
        if 'yaml' in content_type or url.endswith('.yaml') or url.endswith('.yml'):
            try:
                import yaml
                return yaml.safe_load(response.text)
            except ImportError:
                raise OpenAPIFetchError(
                    'YAML parsing requires PyYAML. Install with: pip install pyyaml'
                )

        # Default: try JSON
        return response.json()

    except requests.RequestException as e:
        raise OpenAPIFetchError(f'Failed to fetch spec from {url}: {e}')
    except json.JSONDecodeError as e:
        raise OpenAPIFetchError(f'Failed to parse JSON spec: {e}')


def fetch_and_cache_spec(api: 'ExternalApi') -> dict:
    """Fetch OpenAPI spec and cache it in the database.

    Args:
        api: ExternalApi model instance.

    Returns:
        Parsed OpenAPI spec as dictionary.

    Raises:
        OpenAPIFetchError: If fetching fails.
    """
    spec = fetch_openapi_spec(api.spec_url)

    # Extract base URL from spec if not set
    if not api.base_url and 'servers' in spec:
        servers = spec.get('servers', [])
        if servers and isinstance(servers[0], dict):
            api.base_url = servers[0].get('url', '')

    # Generate documentation
    from v_flask_plugins.api_market.services.doc_generator import (
        generate_quickstart,
        generate_endpoint_docs,
    )

    quickstart_html = generate_quickstart(spec, api)
    endpoints_html = generate_endpoint_docs(spec)

    # Cache the spec and docs
    api.update_spec(
        spec_data=json.dumps(spec),
        documentation_html=f'{quickstart_html}\n\n{endpoints_html}'
    )

    logger.info(f'Cached OpenAPI spec for {api.slug}')
    return spec


def get_cached_spec(api: 'ExternalApi') -> dict | None:
    """Get the cached OpenAPI spec for an API.

    Args:
        api: ExternalApi model instance.

    Returns:
        Parsed spec dict or None if not cached.
    """
    if not api.spec_data:
        return None
    try:
        return json.loads(api.spec_data)
    except json.JSONDecodeError:
        return None


def extract_endpoints(spec: dict) -> list[dict]:
    """Extract endpoint information from an OpenAPI spec.

    Args:
        spec: Parsed OpenAPI spec.

    Returns:
        List of endpoint dictionaries with path, method, summary, etc.
    """
    endpoints = []
    paths = spec.get('paths', {})

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                continue

            endpoint = {
                'path': path,
                'method': method.upper(),
                'summary': details.get('summary', ''),
                'description': details.get('description', ''),
                'operation_id': details.get('operationId', ''),
                'tags': details.get('tags', []),
                'parameters': details.get('parameters', []),
                'request_body': details.get('requestBody'),
                'responses': details.get('responses', {}),
            }
            endpoints.append(endpoint)

    return endpoints


def extract_schemas(spec: dict) -> dict:
    """Extract schema definitions from an OpenAPI spec.

    Args:
        spec: Parsed OpenAPI spec.

    Returns:
        Dictionary of schema name to schema definition.
    """
    components = spec.get('components', {})
    return components.get('schemas', {})
