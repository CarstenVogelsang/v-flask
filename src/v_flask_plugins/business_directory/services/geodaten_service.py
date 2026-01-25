"""Geodaten Service for unternehmensdaten.org API Integration.

Provides methods to fetch and import geographic data:
- Land (Country)
- Bundesland (Federal State)
- Kreis (District)
- Ort (City/Town with PLZ)
"""

import logging

import requests
from slugify import slugify
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from v_flask.extensions import db

from ..models import GeoLand, GeoBundesland, GeoKreis, GeoOrt

logger = logging.getLogger(__name__)


class GeodatenService:
    """Service for unternehmensdaten.org API.

    Provides methods to fetch and import geographic data:
    - Land (Country)
    - Bundesland (Federal State)
    - Kreis (District)
    - Ort (City/Town with PLZ)

    Configuration is loaded from plugin settings:
    - unternehmensdaten_api_key: API key for authentication
    - unternehmensdaten_base_url: API server URL (optional)
    """

    # Defaults
    DEFAULT_BASE_URL = 'https://api.unternehmensdaten.org'
    DEFAULT_ALLOWED_COUNTRIES = ['DE']

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None
    ):
        """Initialize service with API configuration.

        Args:
            api_key: API key for authentication. If not provided,
                     attempts to load from plugin settings.
            base_url: API base URL. Defaults to production API.
        """
        self.api_key = api_key or self._load_api_key()
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.allowed_countries = self.DEFAULT_ALLOWED_COUNTRIES

    def _load_api_key(self) -> str:
        """Load API key from plugin settings."""
        try:
            from v_flask.models import PluginConfig
            config = PluginConfig.get_value(
                'business_directory',
                'unternehmensdaten_api_key'
            )
            return config or ''
        except Exception:
            return ''

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def _get_headers(self) -> dict:
        """Get request headers with API key."""
        return {'X-API-Key': self.api_key}

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((
            requests.ConnectionError,
            requests.Timeout,
            requests.HTTPError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _api_get(self, endpoint: str, params: dict | None = None) -> list[dict]:
        """Make GET request to API with automatic retry.

        Uses exponential backoff: 2s, 4s, 8s, 16s, 30s (max)
        Retries on: ConnectionError, Timeout, HTTPError

        Args:
            endpoint: API endpoint path
            params: Optional query parameters

        Returns:
            List of result dictionaries

        Raises:
            ValueError: If API key not configured
            requests.RequestException: On API errors after all retries
        """
        if not self.is_configured:
            raise ValueError(
                "API key not configured. Set unternehmensdaten_api_key in plugin settings."
            )

        url = f"{self.base_url}{endpoint}"
        response = requests.get(
            url,
            headers=self._get_headers(),
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    # --- API Methods ---

    def get_laender(self) -> list[dict]:
        """Fetch all available countries from API."""
        return self._api_get('/api/v1/partner/geodaten/laender')

    def get_bundeslaender(self, land_code: str) -> list[dict]:
        """Fetch federal states for a country."""
        return self._api_get(
            '/api/v1/partner/geodaten/bundeslaender',
            params={'land_code': land_code}
        )

    def get_kreise(self, bundesland_code: str) -> list[dict]:
        """Fetch districts for a federal state."""
        return self._api_get(
            '/api/v1/partner/geodaten/kreise',
            params={'bundesland_code': bundesland_code}
        )

    def get_orte(self, kreis_code: str) -> list[dict]:
        """Fetch towns/cities for a district."""
        return self._api_get(
            '/api/v1/partner/geodaten/orte',
            params={'kreis_code': kreis_code}
        )

    # --- Sync Methods ---

    def sync_land(self, land_data: dict) -> GeoLand:
        """Create or update a Land from API data."""
        land = db.session.get(GeoLand, land_data['id'])
        if not land:
            land = GeoLand(
                id=land_data['id'],
                code=land_data['code'],
                name=land_data['name'],
                slug=slugify(land_data['name'])
            )
            db.session.add(land)
        else:
            land.code = land_data['code']
            land.name = land_data['name']

        db.session.commit()
        return land

    def sync_bundesland(self, bundesland_data: dict, land_id: str) -> GeoBundesland:
        """Create or update a Bundesland from API data."""
        bundesland = db.session.get(GeoBundesland, bundesland_data['id'])
        if not bundesland:
            bundesland = GeoBundesland(
                id=bundesland_data['id'],
                code=bundesland_data['code'],
                kuerzel=bundesland_data.get('kuerzel'),
                name=bundesland_data['name'],
                slug=slugify(bundesland_data['name']),
                land_id=land_id
            )
            db.session.add(bundesland)
        else:
            bundesland.code = bundesland_data['code']
            bundesland.kuerzel = bundesland_data.get('kuerzel')
            bundesland.name = bundesland_data['name']

        db.session.commit()
        return bundesland

    def sync_kreis(self, kreis_data: dict, bundesland_id: str) -> GeoKreis:
        """Create or update a Kreis from API data."""
        kreis = db.session.get(GeoKreis, kreis_data['id'])
        if not kreis:
            kreis = GeoKreis(
                id=kreis_data['id'],
                code=kreis_data['code'],
                kuerzel=kreis_data.get('kuerzel'),
                name=kreis_data['name'],
                slug=slugify(kreis_data['name']),
                ist_landkreis=kreis_data.get('ist_landkreis', False),
                ist_kreisfreie_stadt=kreis_data.get('ist_kreisfreie_stadt', False),
                einwohner=kreis_data.get('einwohner'),
                bundesland_id=bundesland_id
            )
            db.session.add(kreis)
        else:
            kreis.code = kreis_data['code']
            kreis.kuerzel = kreis_data.get('kuerzel')
            kreis.name = kreis_data['name']
            kreis.ist_landkreis = kreis_data.get('ist_landkreis', False)
            kreis.ist_kreisfreie_stadt = kreis_data.get('ist_kreisfreie_stadt', False)
            kreis.einwohner = kreis_data.get('einwohner')

        db.session.commit()
        return kreis

    # --- Import Methods ---

    def import_laender(self) -> int:
        """Import all Länder from API.

        Returns:
            Number of Länder imported/updated.
        """
        laender_data = self.get_laender()
        count = 0

        for land_data in laender_data:
            if land_data['code'] in self.allowed_countries:
                self.sync_land(land_data)
                count += 1

        return count

    def import_bundeslaender(self, land_id: str) -> int:
        """Import all Bundesländer for a Land.

        Args:
            land_id: GeoLand ID

        Returns:
            Number of Bundesländer imported/updated.
        """
        land = db.session.get(GeoLand, land_id)
        if not land:
            raise ValueError(f"Land not found: {land_id}")

        bundeslaender_data = self.get_bundeslaender(land.code)
        count = 0

        for bl_data in bundeslaender_data:
            self.sync_bundesland(bl_data, land_id)
            count += 1

        return count

    def import_kreise(self, bundesland_id: str) -> int:
        """Import all Kreise for a Bundesland.

        Args:
            bundesland_id: GeoBundesland ID

        Returns:
            Number of Kreise imported/updated.
        """
        bundesland = db.session.get(GeoBundesland, bundesland_id)
        if not bundesland:
            raise ValueError(f"Bundesland not found: {bundesland_id}")

        kreise_data = self.get_kreise(bundesland.code)
        count = 0

        for kreis_data in kreise_data:
            self.sync_kreis(kreis_data, bundesland_id)
            count += 1

        return count

    def import_orte(self, kreis_id: str) -> int:
        """Import all Orte for a Kreis.

        Args:
            kreis_id: GeoKreis ID

        Returns:
            Number of Orte imported.
        """
        kreis = db.session.get(GeoKreis, kreis_id)
        if not kreis:
            raise ValueError(f"Kreis not found: {kreis_id}")

        orte_data = self.get_orte(kreis.code)
        imported_count = 0

        for ort_data in orte_data:
            ort_name = ort_data['name']
            is_hauptort = ort_data.get('ist_hauptort', False)

            ort = db.session.get(GeoOrt, ort_data['id'])
            if not ort:
                ort = GeoOrt(
                    id=ort_data['id'],
                    code=ort_data['code'],
                    name=ort_name,
                    plz=ort_data.get('plz'),
                    lat=ort_data.get('lat'),
                    lng=ort_data.get('lng'),
                    ist_hauptort=is_hauptort,
                    slug=slugify(ort_name) if is_hauptort else None,
                    kreis_id=kreis.id
                )
                db.session.add(ort)
                imported_count += 1
            else:
                ort.code = ort_data['code']
                ort.name = ort_name
                ort.plz = ort_data.get('plz')
                ort.lat = ort_data.get('lat')
                ort.lng = ort_data.get('lng')
                ort.ist_hauptort = is_hauptort
                ort.slug = slugify(ort_name) if is_hauptort else None

        kreis.mark_imported()
        db.session.commit()

        return imported_count

    def import_kreis_hierarchy(self, kreis_code: str) -> dict:
        """Import a Kreis and all parent hierarchy from API.

        Fetches and stores: Land -> Bundesland -> Kreis
        Does NOT import Orte (use import_orte separately).

        Args:
            kreis_code: Kreis code (e.g., 'DE-NW-05154')

        Returns:
            Dict with 'land', 'bundesland', 'kreis' instances
        """
        parts = kreis_code.split('-')
        if len(parts) < 3:
            raise ValueError(f"Invalid kreis_code format: {kreis_code}")

        land_code = parts[0]
        bundesland_code = f"{parts[0]}-{parts[1]}"

        # Fetch and sync Land
        laender = self.get_laender()
        land_data = next((l for l in laender if l['code'] == land_code), None)
        if not land_data:
            raise ValueError(f"Land not found: {land_code}")
        land = self.sync_land(land_data)

        # Fetch and sync Bundesland
        bundeslaender = self.get_bundeslaender(land_code)
        bundesland_data = next(
            (b for b in bundeslaender if b['code'] == bundesland_code),
            None
        )
        if not bundesland_data:
            raise ValueError(f"Bundesland not found: {bundesland_code}")
        bundesland = self.sync_bundesland(bundesland_data, land.id)

        # Fetch and sync Kreis
        kreise = self.get_kreise(bundesland_code)
        kreis_data = next((k for k in kreise if k['code'] == kreis_code), None)
        if not kreis_data:
            raise ValueError(f"Kreis not found: {kreis_code}")
        kreis = self.sync_kreis(kreis_data, bundesland.id)

        return {
            'land': land,
            'bundesland': bundesland,
            'kreis': kreis
        }
