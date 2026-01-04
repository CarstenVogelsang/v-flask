"""Tests for LookupWert model."""

import pytest

from v_flask import db
from v_flask.models import LookupWert, Betreiber


class TestLookupWert:
    """Test cases for LookupWert model."""

    def test_create_global_lookup(self, app):
        """Test creating a global lookup value (no betreiber)."""
        with app.app_context():
            lookup = LookupWert(
                kategorie='status',
                code='open',
                name='Offen',
                farbe='#3b82f6',
                icon='circle'
            )
            db.session.add(lookup)
            db.session.commit()

            assert lookup.id is not None
            assert lookup.is_global() is True
            assert lookup.betreiber_id is None

    def test_create_betreiber_specific_lookup(self, app, betreiber):
        """Test creating a betreiber-specific lookup value."""
        with app.app_context():
            lookup = LookupWert(
                kategorie='status',
                code='in_review',
                name='In Prüfung',
                farbe='#f59e0b',
                betreiber_id=betreiber.id
            )
            db.session.add(lookup)
            db.session.commit()

            assert lookup.id is not None
            assert lookup.is_global() is False
            assert lookup.betreiber_id == betreiber.id

    def test_get_for_kategorie_global_only(self, app):
        """Test getting only global values when no betreiber_id is given."""
        with app.app_context():
            # Create global values
            db.session.add(LookupWert(kategorie='priority', code='low', name='Niedrig'))
            db.session.add(LookupWert(kategorie='priority', code='high', name='Hoch'))
            db.session.commit()

            results = LookupWert.get_for_kategorie('priority')
            assert len(results) == 2
            assert all(r.is_global() for r in results)

    def test_get_for_kategorie_with_betreiber(self, app, betreiber):
        """Test getting global + betreiber-specific values."""
        with app.app_context():
            # Global value
            db.session.add(LookupWert(kategorie='status', code='open', name='Offen'))

            # Betreiber-specific value
            db.session.add(LookupWert(
                kategorie='status',
                code='custom',
                name='Benutzerdefiniert',
                betreiber_id=betreiber.id
            ))
            db.session.commit()

            results = LookupWert.get_for_kategorie('status', betreiber_id=betreiber.id)
            assert len(results) == 2

            codes = [r.code for r in results]
            assert 'open' in codes  # global
            assert 'custom' in codes  # betreiber-specific

    def test_get_for_kategorie_excludes_other_betreiber(self, app):
        """Test that values from other betreiber are excluded."""
        with app.app_context():
            # Create two betreiber
            b1 = Betreiber(name='Betreiber 1')
            b2 = Betreiber(name='Betreiber 2')
            db.session.add_all([b1, b2])
            db.session.commit()

            # Global value
            db.session.add(LookupWert(kategorie='type', code='global', name='Global'))

            # B1-specific value
            db.session.add(LookupWert(
                kategorie='type',
                code='b1_only',
                name='Nur B1',
                betreiber_id=b1.id
            ))

            # B2-specific value
            db.session.add(LookupWert(
                kategorie='type',
                code='b2_only',
                name='Nur B2',
                betreiber_id=b2.id
            ))
            db.session.commit()

            # Query for B1
            results = LookupWert.get_for_kategorie('type', betreiber_id=b1.id)
            codes = [r.code for r in results]

            assert 'global' in codes
            assert 'b1_only' in codes
            assert 'b2_only' not in codes

    def test_get_by_code_prefers_betreiber(self, app, betreiber):
        """Test that get_by_code prefers betreiber-specific over global."""
        with app.app_context():
            # Global value
            db.session.add(LookupWert(
                kategorie='color',
                code='primary',
                name='Global Primary',
                farbe='#000000'
            ))

            # Betreiber-specific value with same code
            db.session.add(LookupWert(
                kategorie='color',
                code='primary',
                name='Betreiber Primary',
                farbe='#ffffff',
                betreiber_id=betreiber.id
            ))
            db.session.commit()

            # Without betreiber_id -> global
            result = LookupWert.get_by_code('color', 'primary')
            assert result.farbe == '#000000'

            # With betreiber_id -> betreiber-specific
            result = LookupWert.get_by_code('color', 'primary', betreiber_id=betreiber.id)
            assert result.farbe == '#ffffff'

    def test_get_by_code_fallback_to_global(self, app, betreiber):
        """Test that get_by_code falls back to global if no betreiber-specific exists."""
        with app.app_context():
            db.session.add(LookupWert(
                kategorie='size',
                code='large',
                name='Groß'
            ))
            db.session.commit()

            result = LookupWert.get_by_code('size', 'large', betreiber_id=betreiber.id)
            assert result is not None
            assert result.name == 'Groß'

    def test_inactive_excluded_by_default(self, app):
        """Test that inactive values are excluded by default."""
        with app.app_context():
            db.session.add(LookupWert(kategorie='cat', code='active', name='Aktiv'))
            db.session.add(LookupWert(kategorie='cat', code='inactive', name='Inaktiv', aktiv=False))
            db.session.commit()

            results = LookupWert.get_for_kategorie('cat')
            assert len(results) == 1
            assert results[0].code == 'active'

    def test_include_inactive(self, app):
        """Test including inactive values when requested."""
        with app.app_context():
            db.session.add(LookupWert(kategorie='cat', code='active', name='Aktiv'))
            db.session.add(LookupWert(kategorie='cat', code='inactive', name='Inaktiv', aktiv=False))
            db.session.commit()

            results = LookupWert.get_for_kategorie('cat', include_inactive=True)
            assert len(results) == 2

    def test_sort_order(self, app):
        """Test that values are sorted by sort_order."""
        with app.app_context():
            db.session.add(LookupWert(kategorie='order', code='third', name='Dritter', sort_order=3))
            db.session.add(LookupWert(kategorie='order', code='first', name='Erster', sort_order=1))
            db.session.add(LookupWert(kategorie='order', code='second', name='Zweiter', sort_order=2))
            db.session.commit()

            results = LookupWert.get_for_kategorie('order')
            codes = [r.code for r in results]

            assert codes == ['first', 'second', 'third']

    def test_get_kategorien(self, app):
        """Test getting all unique category names."""
        with app.app_context():
            db.session.add(LookupWert(kategorie='status', code='a', name='A'))
            db.session.add(LookupWert(kategorie='status', code='b', name='B'))
            db.session.add(LookupWert(kategorie='priority', code='c', name='C'))
            db.session.commit()

            kategorien = LookupWert.get_kategorien()
            assert sorted(kategorien) == ['priority', 'status']

    def test_to_dict(self, app):
        """Test dictionary representation."""
        with app.app_context():
            lookup = LookupWert(
                kategorie='test',
                code='test_code',
                name='Test Name',
                farbe='#123456',
                icon='star',
                sort_order=5
            )
            db.session.add(lookup)
            db.session.commit()

            d = lookup.to_dict()
            assert d['kategorie'] == 'test'
            assert d['code'] == 'test_code'
            assert d['name'] == 'Test Name'
            assert d['farbe'] == '#123456'
            assert d['icon'] == 'star'
            assert d['sort_order'] == 5
            assert d['is_global'] is True

    def test_unique_constraint(self, app, betreiber):
        """Test unique constraint on (kategorie, code, betreiber_id)."""
        from sqlalchemy.exc import IntegrityError

        with app.app_context():
            # Create first entry for betreiber
            db.session.add(LookupWert(
                kategorie='dup',
                code='same',
                name='First',
                betreiber_id=betreiber.id
            ))
            db.session.commit()

            # Same code+kategorie+betreiber should fail
            db.session.add(LookupWert(
                kategorie='dup',
                code='same',
                name='Second',
                betreiber_id=betreiber.id
            ))
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            # But same code for global (NULL betreiber_id) should work
            db.session.add(LookupWert(
                kategorie='dup',
                code='same',
                name='Global Version'
            ))
            db.session.commit()  # Should succeed
