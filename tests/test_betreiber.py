"""Tests for Betreiber model."""

import pytest

from v_flask import db
from v_flask.models import Betreiber


class TestBetreiber:
    """Test cases for Betreiber model."""

    def test_create_betreiber(self, app):
        """Test creating a basic Betreiber."""
        with app.app_context():
            betreiber = Betreiber(
                name='Test GmbH',
                website='https://test.de'
            )
            db.session.add(betreiber)
            db.session.commit()

            assert betreiber.id is not None
            assert betreiber.name == 'Test GmbH'
            assert betreiber.website == 'https://test.de'

    def test_create_betreiber_with_email(self, app):
        """Test creating a Betreiber with email address."""
        with app.app_context():
            betreiber = Betreiber(
                name='Mail Corp',
                email='kontakt@mail-corp.de',
                website='https://mail-corp.de'
            )
            db.session.add(betreiber)
            db.session.commit()

            assert betreiber.id is not None
            assert betreiber.email == 'kontakt@mail-corp.de'

    def test_email_nullable(self, app):
        """Test that email is optional (nullable)."""
        with app.app_context():
            betreiber = Betreiber(name='No Email Inc')
            db.session.add(betreiber)
            db.session.commit()

            assert betreiber.id is not None
            assert betreiber.email is None

    def test_email_in_to_dict(self, app):
        """Test that email is included in to_dict output."""
        with app.app_context():
            betreiber = Betreiber(
                name='Dict Test',
                email='test@example.com',
                primary_color='#ff0000'
            )
            db.session.add(betreiber)
            db.session.commit()

            d = betreiber.to_dict()
            assert 'email' in d
            assert d['email'] == 'test@example.com'

    def test_email_none_in_to_dict(self, app):
        """Test that email is None in to_dict when not set."""
        with app.app_context():
            betreiber = Betreiber(name='No Email Dict')
            db.session.add(betreiber)
            db.session.commit()

            d = betreiber.to_dict()
            assert 'email' in d
            assert d['email'] is None

    def test_default_colors(self, app):
        """Test default CI colors."""
        with app.app_context():
            betreiber = Betreiber(name='Defaults')
            db.session.add(betreiber)
            db.session.commit()

            assert betreiber.primary_color == '#3b82f6'
            assert betreiber.secondary_color == '#64748b'
            assert betreiber.font_family == 'Inter'

    def test_css_variables(self, app):
        """Test CSS variables generation."""
        with app.app_context():
            betreiber = Betreiber(
                name='Styled',
                primary_color='#123456',
                secondary_color='#654321',
                font_family='Roboto'
            )
            db.session.add(betreiber)
            db.session.commit()

            css = betreiber.get_css_variables()
            assert '--v-primary: #123456' in css
            assert '--v-secondary: #654321' in css
            assert "'Roboto'" in css

    def test_repr(self, app):
        """Test string representation."""
        with app.app_context():
            betreiber = Betreiber(name='Repr Test')
            db.session.add(betreiber)
            db.session.commit()

            assert repr(betreiber) == '<Betreiber Repr Test>'

    def test_update_email(self, app):
        """Test updating email address."""
        with app.app_context():
            betreiber = Betreiber(name='Update Test')
            db.session.add(betreiber)
            db.session.commit()

            assert betreiber.email is None

            betreiber.email = 'updated@test.de'
            db.session.commit()

            # Fetch fresh from DB
            fresh = db.session.get(Betreiber, betreiber.id)
            assert fresh.email == 'updated@test.de'
