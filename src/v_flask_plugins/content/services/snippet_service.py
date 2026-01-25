"""Text snippet management service."""
import json
from pathlib import Path
from typing import Any

from flask import current_app


class SnippetService:
    """Service for managing text snippets (Textbausteine)."""

    def __init__(self):
        self._system_snippets_cache: dict[str, list[dict]] | None = None

    def _get_snippets_path(self) -> Path:
        """Get the path to the snippets directory."""
        return Path(__file__).parent.parent / 'data' / 'snippets'

    def _load_json_file(self, file_path: Path) -> list[dict]:
        """Load snippets from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            current_app.logger.error(f'Error parsing {file_path}: {e}')
            return []

    def get_system_snippets(self, kategorie: str | None = None, branche: str | None = None) -> list[dict]:
        """Get system-provided snippets from JSON files.

        Args:
            kategorie: Filter by category (e.g., 'startseite', 'ueber_uns')
            branche: Filter by industry (e.g., 'gastronomie'), None for general

        Returns:
            List of snippet dictionaries
        """
        snippets_path = self._get_snippets_path()
        all_snippets = []

        # Load general snippets
        allgemein_path = snippets_path / 'allgemein'
        if allgemein_path.exists():
            for json_file in allgemein_path.glob('*.json'):
                file_snippets = self._load_json_file(json_file)
                for snippet in file_snippets:
                    snippet['source'] = 'system'
                    snippet['branche'] = None
                    if kategorie is None or snippet.get('kategorie') == kategorie:
                        all_snippets.append(snippet)

        # Load industry-specific snippets
        if branche:
            branche_path = snippets_path / 'branchen' / f'{branche}.json'
            if branche_path.exists():
                branche_snippets = self._load_json_file(branche_path)
                for snippet in branche_snippets:
                    snippet['source'] = 'system'
                    snippet['branche'] = branche
                    if kategorie is None or snippet.get('kategorie') == kategorie:
                        all_snippets.append(snippet)

        return all_snippets

    def get_user_snippets(
        self,
        betreiber_id: int | None = None,
        kategorie: str | None = None
    ) -> list[dict]:
        """Get user-created snippets from database.

        Args:
            betreiber_id: Filter by operator ID
            kategorie: Filter by category

        Returns:
            List of snippet dictionaries
        """
        from v_flask_plugins.content.models import TextSnippet

        query = TextSnippet.query.filter_by(source='user')

        if betreiber_id is not None:
            query = query.filter(
                (TextSnippet.betreiber_id == betreiber_id) |
                (TextSnippet.betreiber_id.is_(None))
            )

        if kategorie:
            query = query.filter_by(kategorie=kategorie)

        snippets = query.order_by(TextSnippet.name).all()

        return [
            {
                'id': s.id,
                'name': s.name,
                'kategorie': s.kategorie,
                'branche': s.branche,
                'titel': s.titel,
                'text': s.text,
                'source': s.source,
            }
            for s in snippets
        ]

    def get_all_snippets(
        self,
        kategorie: str | None = None,
        branche: str | None = None,
        betreiber_id: int | None = None
    ) -> list[dict]:
        """Get all available snippets (system + user).

        Args:
            kategorie: Filter by category
            branche: Filter by industry (for system snippets)
            betreiber_id: Filter by operator ID (for user snippets)

        Returns:
            Combined list of all snippets, grouped by source
        """
        system_snippets = self.get_system_snippets(kategorie, branche)
        user_snippets = self.get_user_snippets(betreiber_id, kategorie)

        return system_snippets + user_snippets

    def get_available_categories(self) -> list[dict]:
        """Get list of available snippet categories.

        Returns:
            List of category definitions with id and name
        """
        return [
            {'id': 'startseite', 'name': 'Startseite'},
            {'id': 'ueber_uns', 'name': 'Über uns'},
            {'id': 'leistungen', 'name': 'Leistungen'},
            {'id': 'team', 'name': 'Team'},
            {'id': 'kontakt', 'name': 'Kontakt'},
            {'id': 'allgemein', 'name': 'Allgemein'},
        ]

    def get_available_industries(self) -> list[dict]:
        """Get list of available industries (Branchen).

        Returns:
            List of industry definitions with id and name
        """
        return [
            {'id': 'gastronomie', 'name': 'Gastronomie'},
            {'id': 'einzelhandel', 'name': 'Einzelhandel'},
            {'id': 'handwerk', 'name': 'Handwerk'},
            {'id': 'dienstleistung', 'name': 'Dienstleistung'},
        ]

    def create_snippet(
        self,
        name: str,
        kategorie: str,
        titel: str,
        text: str,
        betreiber_id: int | None = None,
        branche: str | None = None
    ) -> Any:
        """Create a new user snippet.

        Args:
            name: Internal name for the snippet
            kategorie: Category (e.g., 'startseite')
            titel: Title text
            text: Body text
            betreiber_id: Owner operator ID (None for global)
            branche: Industry filter (optional)

        Returns:
            Created TextSnippet model instance
        """
        from v_flask import db
        from v_flask_plugins.content.models import TextSnippet

        snippet = TextSnippet(
            name=name,
            kategorie=kategorie,
            titel=titel,
            text=text,
            source='user',
            betreiber_id=betreiber_id,
            branche=branche,
        )

        db.session.add(snippet)
        db.session.commit()

        return snippet

    def seed_system_snippets(self) -> int:
        """Seed system snippets from JSON files into the database.

        This is useful for making system snippets editable or for
        environments where file-based snippets aren't accessible.

        Returns:
            Number of snippets created
        """
        from v_flask import db
        from v_flask_plugins.content.models import TextSnippet

        count = 0
        system_snippets = self.get_system_snippets()

        for snippet_data in system_snippets:
            # Check if already exists
            existing = TextSnippet.query.filter_by(
                name=snippet_data.get('name'),
                source='system'
            ).first()

            if not existing:
                snippet = TextSnippet(
                    name=snippet_data.get('name', 'Unbenannt'),
                    kategorie=snippet_data.get('kategorie', 'allgemein'),
                    branche=snippet_data.get('branche'),
                    titel=snippet_data.get('titel', ''),
                    text=snippet_data.get('text', ''),
                    source='system',
                    betreiber_id=None,
                )
                db.session.add(snippet)
                count += 1

        db.session.commit()
        return count


# Singleton instance
snippet_service = SnippetService()
