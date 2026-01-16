"""Database models for the Datenschutz plugin.

Provides:
    - DatenschutzConfig: Main configuration with activated Bausteine
    - DatenschutzVersion: Version history for compliance audits
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from v_flask.extensions import db


class DatenschutzConfig(db.Model):
    """Main configuration for the privacy policy.

    Stores:
        - Verantwortlicher (controller) information
        - Datenschutzbeauftragter (DPO) if applicable
        - List of activated Bausteine (text modules)
        - Custom text overrides
    """

    __tablename__ = 'datenschutz_config'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Verantwortlicher (DSGVO Art. 13 Abs. 1 lit. a)
    verantwortlicher_name: Mapped[str | None] = mapped_column(String(200))
    verantwortlicher_strasse: Mapped[str | None] = mapped_column(String(200))
    verantwortlicher_plz: Mapped[str | None] = mapped_column(String(10))
    verantwortlicher_ort: Mapped[str | None] = mapped_column(String(100))
    verantwortlicher_land: Mapped[str | None] = mapped_column(
        String(100), default='Deutschland'
    )
    verantwortlicher_email: Mapped[str | None] = mapped_column(String(200))
    verantwortlicher_telefon: Mapped[str | None] = mapped_column(String(50))

    # Datenschutzbeauftragter (DSGVO Art. 13 Abs. 1 lit. b)
    dsb_vorhanden: Mapped[bool] = mapped_column(Boolean, default=False)
    dsb_name: Mapped[str | None] = mapped_column(String(200))
    dsb_email: Mapped[str | None] = mapped_column(String(200))
    dsb_telefon: Mapped[str | None] = mapped_column(String(50))
    dsb_extern: Mapped[bool] = mapped_column(Boolean, default=False)

    # Activated Bausteine (text modules)
    # Stored as JSON list: ["server_logs", "kontaktformular", "google_analytics"]
    aktivierte_bausteine: Mapped[list] = mapped_column(JSON, default=list)

    # Custom text overrides for specific Bausteine
    # Stored as JSON dict: {"server_logs": "Custom text...", ...}
    custom_texte: Mapped[dict] = mapped_column(JSON, default=dict)

    # Baustein-specific configuration (e.g., tracking IDs, provider names)
    # Stored as JSON dict: {"google_analytics": {"tracking_id": "G-..."}, ...}
    baustein_config: Mapped[dict] = mapped_column(JSON, default=dict)

    # Metadata
    version: Mapped[int] = mapped_column(Integer, default=1)
    letzte_aktualisierung: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationship to version history
    versionen: Mapped[list['DatenschutzVersion']] = relationship(
        'DatenschutzVersion', back_populates='config', cascade='all, delete-orphan'
    )

    def get_verantwortlicher_adresse(self) -> str | None:
        """Get formatted address of the controller."""
        parts = []
        if self.verantwortlicher_strasse:
            parts.append(self.verantwortlicher_strasse)
        if self.verantwortlicher_plz and self.verantwortlicher_ort:
            parts.append(f'{self.verantwortlicher_plz} {self.verantwortlicher_ort}')
        if self.verantwortlicher_land and self.verantwortlicher_land != 'Deutschland':
            parts.append(self.verantwortlicher_land)
        return '\n'.join(parts) if parts else None

    def is_baustein_aktiv(self, baustein_id: str) -> bool:
        """Check if a Baustein is activated."""
        return baustein_id in (self.aktivierte_bausteine or [])

    def get_baustein_config(self, baustein_id: str) -> dict:
        """Get configuration for a specific Baustein."""
        return (self.baustein_config or {}).get(baustein_id, {})

    def set_baustein_config(self, baustein_id: str, config: dict) -> None:
        """Set configuration for a specific Baustein."""
        if self.baustein_config is None:
            self.baustein_config = {}
        self.baustein_config[baustein_id] = config

    def get_custom_text(self, baustein_id: str) -> str | None:
        """Get custom text override for a Baustein."""
        return (self.custom_texte or {}).get(baustein_id)

    def aktiviere_baustein(self, baustein_id: str) -> None:
        """Activate a Baustein."""
        if self.aktivierte_bausteine is None:
            self.aktivierte_bausteine = []
        if baustein_id not in self.aktivierte_bausteine:
            self.aktivierte_bausteine = [*self.aktivierte_bausteine, baustein_id]

    def deaktiviere_baustein(self, baustein_id: str) -> None:
        """Deactivate a Baustein."""
        if self.aktivierte_bausteine and baustein_id in self.aktivierte_bausteine:
            self.aktivierte_bausteine = [
                b for b in self.aktivierte_bausteine if b != baustein_id
            ]

    def create_version_snapshot(self, changed_by: str | None = None) -> None:
        """Create a version snapshot before saving changes."""
        snapshot = {
            'verantwortlicher': {
                'name': self.verantwortlicher_name,
                'strasse': self.verantwortlicher_strasse,
                'plz': self.verantwortlicher_plz,
                'ort': self.verantwortlicher_ort,
                'land': self.verantwortlicher_land,
                'email': self.verantwortlicher_email,
                'telefon': self.verantwortlicher_telefon,
            },
            'dsb': {
                'vorhanden': self.dsb_vorhanden,
                'name': self.dsb_name,
                'email': self.dsb_email,
                'telefon': self.dsb_telefon,
                'extern': self.dsb_extern,
            },
            'aktivierte_bausteine': self.aktivierte_bausteine,
            'baustein_config': self.baustein_config,
            'custom_texte': self.custom_texte,
        }

        version = DatenschutzVersion(
            config=self,
            version=self.version,
            snapshot=snapshot,
            changed_by=changed_by,
        )
        self.versionen.append(version)
        self.version += 1
        self.letzte_aktualisierung = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'verantwortlicher': {
                'name': self.verantwortlicher_name,
                'strasse': self.verantwortlicher_strasse,
                'plz': self.verantwortlicher_plz,
                'ort': self.verantwortlicher_ort,
                'land': self.verantwortlicher_land,
                'email': self.verantwortlicher_email,
                'telefon': self.verantwortlicher_telefon,
            },
            'dsb': {
                'vorhanden': self.dsb_vorhanden,
                'name': self.dsb_name,
                'email': self.dsb_email,
                'telefon': self.dsb_telefon,
                'extern': self.dsb_extern,
            },
            'aktivierte_bausteine': self.aktivierte_bausteine,
            'version': self.version,
            'letzte_aktualisierung': self.letzte_aktualisierung.isoformat()
            if self.letzte_aktualisierung
            else None,
        }

    def __repr__(self) -> str:
        return f'<DatenschutzConfig v{self.version}>'


class DatenschutzVersion(db.Model):
    """Version history for compliance audits.

    Stores complete snapshots of the privacy policy configuration
    whenever changes are saved.
    """

    __tablename__ = 'datenschutz_version'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('datenschutz_config.id'), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Complete configuration snapshot as JSON
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    changed_by: Mapped[str | None] = mapped_column(String(200))

    # Relationship back to config
    config: Mapped['DatenschutzConfig'] = relationship(
        'DatenschutzConfig', back_populates='versionen'
    )

    def __repr__(self) -> str:
        return f'<DatenschutzVersion {self.version} @ {self.created_at}>'
