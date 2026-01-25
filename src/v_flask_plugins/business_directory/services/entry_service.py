"""Entry Service for DirectoryEntry Operations.

Business logic for creating, updating, and managing directory entries.
"""

from slugify import slugify

from v_flask.extensions import db

from ..models import DirectoryType, DirectoryEntry, GeoOrt


class EntryService:
    """Service for DirectoryEntry operations.

    Provides methods for:
    - Creating entries with validation
    - Updating entries
    - Managing entry status
    - Searching and filtering
    """

    @staticmethod
    def create_entry(
        directory_type: DirectoryType,
        name: str,
        geo_ort: GeoOrt | None = None,
        owner_id: int | None = None,
        **kwargs
    ) -> DirectoryEntry:
        """Create a new directory entry.

        Args:
            directory_type: The DirectoryType for this entry.
            name: Entry name (required).
            geo_ort: Optional GeoOrt for location.
            owner_id: Optional owner user ID.
            **kwargs: Additional fields (strasse, telefon, email, etc.)

        Returns:
            Created DirectoryEntry instance.
        """
        entry = DirectoryEntry(
            directory_type_id=directory_type.id,
            name=name,
            geo_ort_id=geo_ort.id if geo_ort else None,
            owner_id=owner_id,
            strasse=kwargs.get('strasse'),
            telefon=kwargs.get('telefon'),
            email=kwargs.get('email'),
            website=kwargs.get('website'),
            kurzbeschreibung=kwargs.get('kurzbeschreibung'),
            active=kwargs.get('active', False),
            verified=kwargs.get('verified', False),
            self_managed=kwargs.get('self_managed', bool(owner_id)),
        )

        # Generate slug
        entry.generate_slug()

        # Handle type-specific data
        data = kwargs.get('data', {})
        if directory_type.field_schema:
            # Validate data against schema
            validated_data = {}
            for field_name, field_def in directory_type.field_schema.items():
                if field_name in data:
                    validated_data[field_name] = data[field_name]
            entry.data = validated_data
        else:
            entry.data = data

        db.session.add(entry)
        db.session.commit()

        return entry

    @staticmethod
    def update_entry(
        entry: DirectoryEntry,
        **kwargs
    ) -> DirectoryEntry:
        """Update an existing entry.

        Args:
            entry: DirectoryEntry to update.
            **kwargs: Fields to update.

        Returns:
            Updated DirectoryEntry instance.
        """
        # Update basic fields
        basic_fields = [
            'name', 'strasse', 'telefon', 'email', 'website',
            'kurzbeschreibung', 'active', 'verified', 'self_managed'
        ]

        for field in basic_fields:
            if field in kwargs:
                setattr(entry, field, kwargs[field])

        # Regenerate slug if name changed
        if 'name' in kwargs:
            entry.generate_slug()

        # Update geo_ort
        if 'geo_ort_id' in kwargs:
            entry.geo_ort_id = kwargs['geo_ort_id']

        # Update type-specific data
        if 'data' in kwargs:
            directory_type = entry.directory_type
            if directory_type and directory_type.field_schema:
                validated_data = {}
                for field_name, field_def in directory_type.field_schema.items():
                    if field_name in kwargs['data']:
                        validated_data[field_name] = kwargs['data'][field_name]
                entry.data = validated_data
            else:
                entry.data = kwargs['data']

        db.session.commit()
        return entry

    @staticmethod
    def activate_entry(entry: DirectoryEntry) -> None:
        """Activate an entry."""
        entry.active = True
        db.session.commit()

    @staticmethod
    def deactivate_entry(entry: DirectoryEntry) -> None:
        """Deactivate an entry."""
        entry.active = False
        db.session.commit()

    @staticmethod
    def verify_entry(entry: DirectoryEntry) -> None:
        """Mark an entry as verified."""
        entry.verified = True
        db.session.commit()

    @staticmethod
    def transfer_ownership(
        entry: DirectoryEntry,
        new_owner_id: int
    ) -> None:
        """Transfer entry ownership to a new user.

        Args:
            entry: DirectoryEntry to transfer.
            new_owner_id: New owner's user ID.
        """
        entry.owner_id = new_owner_id
        entry.self_managed = True
        db.session.commit()

    @staticmethod
    def remove_ownership(entry: DirectoryEntry) -> None:
        """Remove ownership from an entry."""
        entry.owner_id = None
        entry.self_managed = False
        db.session.commit()

    @staticmethod
    def find_by_plz(
        plz: str,
        directory_type_id: int | None = None,
        active_only: bool = True
    ) -> list[DirectoryEntry]:
        """Find entries by PLZ.

        Args:
            plz: Postal code to search.
            directory_type_id: Optional filter by type.
            active_only: Only return active entries.

        Returns:
            List of matching DirectoryEntry instances.
        """
        orte = GeoOrt.query.filter_by(plz=plz).all()
        ort_ids = [o.id for o in orte]

        if not ort_ids:
            return []

        query = DirectoryEntry.query.filter(
            DirectoryEntry.geo_ort_id.in_(ort_ids)
        )

        if directory_type_id:
            query = query.filter_by(directory_type_id=directory_type_id)

        if active_only:
            query = query.filter_by(active=True)

        return query.order_by(DirectoryEntry.name).all()

    @staticmethod
    def search(
        query_string: str,
        directory_type_id: int | None = None,
        active_only: bool = True,
        limit: int = 50
    ) -> list[DirectoryEntry]:
        """Search entries by name and description.

        Args:
            query_string: Search text.
            directory_type_id: Optional filter by type.
            active_only: Only return active entries.
            limit: Maximum results.

        Returns:
            List of matching DirectoryEntry instances.
        """
        query = DirectoryEntry.query.filter(
            db.or_(
                DirectoryEntry.name.ilike(f'%{query_string}%'),
                DirectoryEntry.kurzbeschreibung.ilike(f'%{query_string}%'),
            )
        )

        if directory_type_id:
            query = query.filter_by(directory_type_id=directory_type_id)

        if active_only:
            query = query.filter_by(active=True)

        return query.order_by(DirectoryEntry.name).limit(limit).all()

    @staticmethod
    def get_pending_review(
        directory_type_id: int | None = None,
        limit: int = 50
    ) -> list[DirectoryEntry]:
        """Get entries pending review (inactive, not verified).

        Args:
            directory_type_id: Optional filter by type.
            limit: Maximum results.

        Returns:
            List of DirectoryEntry instances pending review.
        """
        query = DirectoryEntry.query.filter_by(active=False)

        if directory_type_id:
            query = query.filter_by(directory_type_id=directory_type_id)

        return query.order_by(DirectoryEntry.created_at.asc()).limit(limit).all()

    @staticmethod
    def get_by_owner(
        owner_id: int,
        directory_type_id: int | None = None
    ) -> list[DirectoryEntry]:
        """Get all entries owned by a user.

        Args:
            owner_id: Owner's user ID.
            directory_type_id: Optional filter by type.

        Returns:
            List of DirectoryEntry instances.
        """
        query = DirectoryEntry.query.filter_by(owner_id=owner_id)

        if directory_type_id:
            query = query.filter_by(directory_type_id=directory_type_id)

        return query.order_by(DirectoryEntry.name).all()

    @staticmethod
    def count_by_type() -> dict[str, int]:
        """Get entry count per directory type.

        Returns:
            Dict mapping type slug to count.
        """
        result = {}
        types = DirectoryType.query.filter_by(active=True).all()

        for t in types:
            result[t.slug] = t.entries.filter_by(active=True).count()

        return result
