"""CRM API Client - HTTP client for UDO API communication.

This client uses the host app's configuration for the API base URL
and the session for authentication tokens.
"""
from __future__ import annotations

from typing import Any

import httpx
from flask import current_app, session


class CrmApiClient:
    """HTTP Client for CRM-related API calls to UDO API.

    Uses:
    - UDO_API_BASE_URL from Flask config
    - udo_access_token from Flask session
    """

    def __init__(self, timeout: int = 30):
        """Initialize the client.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout

    def _get_base_url(self) -> str:
        """Get UDO API base URL from app config."""
        return current_app.config.get(
            'UDO_API_BASE_URL',
            'http://localhost:8001/api/v1'
        )

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with auth token from session."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        # Use udo_ prefix to match UdoApiClient in host app
        token = session.get('udo_access_token')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response.

        Args:
            response: httpx Response object.

        Returns:
            Parsed JSON response.

        Raises:
            httpx.HTTPStatusError: If response indicates an error.
        """
        response.raise_for_status()
        if response.status_code == 204:
            return {}
        return response.json()

    # ============ Generic HTTP Methods ============

    def get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """Make GET request to API.

        Args:
            endpoint: API endpoint (e.g., '/unternehmen').
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        url = f"{self._get_base_url()}{endpoint}"
        response = httpx.get(
            url,
            params=params,
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def post(self, endpoint: str, data: dict | None = None) -> dict[str, Any]:
        """Make POST request to API.

        Args:
            endpoint: API endpoint.
            data: JSON body data.

        Returns:
            Parsed JSON response.
        """
        url = f"{self._get_base_url()}{endpoint}"
        response = httpx.post(
            url,
            json=data,
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def patch(self, endpoint: str, data: dict | None = None) -> dict[str, Any]:
        """Make PATCH request to API.

        Args:
            endpoint: API endpoint.
            data: JSON body data.

        Returns:
            Parsed JSON response.
        """
        url = f"{self._get_base_url()}{endpoint}"
        response = httpx.patch(
            url,
            json=data,
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def delete(self, endpoint: str) -> dict[str, Any]:
        """Make DELETE request to API.

        Args:
            endpoint: API endpoint.

        Returns:
            Empty dict on success.
        """
        url = f"{self._get_base_url()}{endpoint}"
        response = httpx.delete(
            url,
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    # ============ Unternehmen Methods ============

    def list_unternehmen(
        self,
        suche: str | None = None,
        geo_ort_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        """List companies with optional filters.

        Args:
            suche: Search term for kurzname/firmierung.
            geo_ort_id: Filter by GeoOrt UUID.
            skip: Pagination offset.
            limit: Pagination limit.

        Returns:
            Dict with 'items' and 'total'.
        """
        params = {'skip': skip, 'limit': limit}
        if suche:
            params['suche'] = suche
        if geo_ort_id:
            params['geo_ort_id'] = geo_ort_id
        return self.get('/unternehmen', params=params)

    def get_unternehmen(self, unternehmen_id: str) -> dict[str, Any]:
        """Get a single company by ID.

        Args:
            unternehmen_id: UUID of the company.

        Returns:
            Company details with geo hierarchy.
        """
        return self.get(f'/unternehmen/{unternehmen_id}')

    def create_unternehmen(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new company.

        Args:
            data: Company data (kurzname required).

        Returns:
            Created company.
        """
        return self.post('/unternehmen', data=data)

    def update_unternehmen(
        self,
        unternehmen_id: str,
        data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a company.

        Args:
            unternehmen_id: UUID of the company.
            data: Fields to update.

        Returns:
            Updated company.
        """
        return self.patch(f'/unternehmen/{unternehmen_id}', data=data)

    def delete_unternehmen(self, unternehmen_id: str) -> dict[str, Any]:
        """Delete a company.

        Args:
            unternehmen_id: UUID of the company.

        Returns:
            Empty dict on success.
        """
        return self.delete(f'/unternehmen/{unternehmen_id}')

    def get_unternehmen_count(self) -> int:
        """Get total number of companies.

        Returns:
            Total count.
        """
        result = self.get('/unternehmen/stats/count')
        return result.get('total', 0)

    # ============ Organisation Methods ============

    def list_organisationen(
        self,
        suche: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        """List organisations.

        Args:
            suche: Search term for kurzname.
            skip: Pagination offset.
            limit: Pagination limit.

        Returns:
            Dict with 'items' and 'total'.
        """
        params = {'skip': skip, 'limit': limit}
        if suche:
            params['suche'] = suche
        return self.get('/organisationen', params=params)

    def get_organisation(self, organisation_id: str) -> dict[str, Any]:
        """Get a single organisation by ID.

        Args:
            organisation_id: UUID of the organisation.

        Returns:
            Organisation details.
        """
        return self.get(f'/organisationen/{organisation_id}')

    def create_organisation(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new organisation.

        Args:
            data: Organisation data (kurzname required).

        Returns:
            Created organisation.
        """
        return self.post('/organisationen', data=data)

    def update_organisation(
        self,
        organisation_id: str,
        data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an organisation.

        Args:
            organisation_id: UUID of the organisation.
            data: Fields to update.

        Returns:
            Updated organisation.
        """
        return self.patch(f'/organisationen/{organisation_id}', data=data)

    def delete_organisation(self, organisation_id: str) -> dict[str, Any]:
        """Delete an organisation.

        Args:
            organisation_id: UUID of the organisation.

        Returns:
            Empty dict on success.
        """
        return self.delete(f'/organisationen/{organisation_id}')

    # ============ Kontakt Methods ============

    def list_kontakte(
        self,
        unternehmen_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        """List contacts for a company.

        Args:
            unternehmen_id: UUID of the company.
            skip: Pagination offset.
            limit: Pagination limit.

        Returns:
            Dict with 'items' and 'total'.
        """
        params = {'skip': skip, 'limit': limit}
        return self.get(f'/unternehmen/{unternehmen_id}/kontakte', params=params)

    def get_kontakt(
        self,
        unternehmen_id: str,
        kontakt_id: str
    ) -> dict[str, Any]:
        """Get a single contact.

        Args:
            unternehmen_id: UUID of the company.
            kontakt_id: UUID of the contact.

        Returns:
            Contact details.
        """
        return self.get(f'/unternehmen/{unternehmen_id}/kontakte/{kontakt_id}')

    def create_kontakt(
        self,
        unternehmen_id: str,
        data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new contact for a company.

        Args:
            unternehmen_id: UUID of the company.
            data: Contact data (vorname, nachname required).

        Returns:
            Created contact.
        """
        return self.post(f'/unternehmen/{unternehmen_id}/kontakte', data=data)

    def update_kontakt(
        self,
        unternehmen_id: str,
        kontakt_id: str,
        data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a contact.

        Args:
            unternehmen_id: UUID of the company.
            kontakt_id: UUID of the contact.
            data: Fields to update.

        Returns:
            Updated contact.
        """
        return self.patch(
            f'/unternehmen/{unternehmen_id}/kontakte/{kontakt_id}',
            data=data
        )

    def delete_kontakt(
        self,
        unternehmen_id: str,
        kontakt_id: str
    ) -> dict[str, Any]:
        """Delete a contact.

        Args:
            unternehmen_id: UUID of the company.
            kontakt_id: UUID of the contact.

        Returns:
            Empty dict on success.
        """
        return self.delete(f'/unternehmen/{unternehmen_id}/kontakte/{kontakt_id}')

    # ============ Geo Methods ============

    def get_geo_laender(self) -> list[dict[str, Any]]:
        """Get all countries.

        Returns:
            List of countries.
        """
        result = self.get('/geo/laender')
        return result.get('items', [])

    def get_geo_bundeslaender(self, land_id: str) -> list[dict[str, Any]]:
        """Get federal states for a country.

        Args:
            land_id: UUID of the country.

        Returns:
            List of federal states.
        """
        result = self.get(f'/geo/laender/{land_id}/bundeslaender')
        return result.get('items', [])

    def get_geo_kreise(self, bundesland_id: str) -> list[dict[str, Any]]:
        """Get districts for a federal state.

        Args:
            bundesland_id: UUID of the federal state.

        Returns:
            List of districts.
        """
        result = self.get(f'/geo/bundeslaender/{bundesland_id}/kreise')
        return result.get('items', [])

    def get_geo_orte(self, kreis_id: str) -> list[dict[str, Any]]:
        """Get cities/municipalities for a district.

        Args:
            kreis_id: UUID of the district.

        Returns:
            List of cities/municipalities.
        """
        result = self.get(f'/geo/kreise/{kreis_id}/orte')
        return result.get('items', [])

    def search_geo_orte(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search for cities/municipalities by name.

        Args:
            query: Search term.
            limit: Maximum results.

        Returns:
            List of matching cities/municipalities.
        """
        result = self.get('/geo/orte', params={'suche': query, 'limit': limit})
        return result.get('items', [])


# Singleton instance for easy access
crm_client = CrmApiClient()
