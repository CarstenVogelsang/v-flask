"""Business Directory CLI Commands."""

import click
from flask.cli import with_appcontext

from v_flask.extensions import db


@click.group('directory')
def directory_cli():
    """Business Directory management commands."""
    pass


@directory_cli.command('seed-types')
@with_appcontext
def seed_types():
    """Create example directory types."""
    from .models import DirectoryType

    types_data = [
        {
            'slug': 'haendler',
            'name': 'Spielwarenhändler',
            'name_singular': 'Händler',
            'name_plural': 'Händler',
            'icon': 'ti-building-store',
            'description': 'Lokale Spielwarengeschäfte in Ihrer Nähe',
            'field_schema': {
                'oeffnungszeiten': {
                    'type': 'opening_hours',
                    'label': 'Öffnungszeiten',
                    'required': True,
                    'show_in_detail': True,
                },
                'marken': {
                    'type': 'text',
                    'label': 'Geführte Marken',
                    'required': False,
                    'show_in_detail': True,
                },
                'parkplaetze': {
                    'type': 'boolean',
                    'label': 'Parkplätze vorhanden',
                    'show_in_detail': True,
                },
            },
        },
        {
            'slug': 'hersteller',
            'name': 'Spielwarenhersteller',
            'name_singular': 'Hersteller',
            'name_plural': 'Hersteller',
            'icon': 'ti-building-factory-2',
            'description': 'Spielwarenmarken und Produzenten',
            'field_schema': {
                'marken': {
                    'type': 'text',
                    'label': 'Unsere Marken',
                    'required': True,
                    'show_in_detail': True,
                },
                'gruendungsjahr': {
                    'type': 'number',
                    'label': 'Gründungsjahr',
                    'show_in_detail': True,
                },
                'mitarbeiter': {
                    'type': 'select',
                    'label': 'Unternehmensgröße',
                    'options': ['1-10', '11-50', '51-200', '200+'],
                    'show_in_detail': True,
                },
            },
        },
    ]

    created = 0
    for data in types_data:
        existing = DirectoryType.get_by_slug(data['slug'])
        if not existing:
            directory_type = DirectoryType(**data)
            db.session.add(directory_type)
            created += 1
            click.echo(f"Created: {data['name']}")
        else:
            click.echo(f"Exists: {data['name']}")

    db.session.commit()
    click.echo(f"\nCreated {created} directory type(s).")


@directory_cli.command('import-geodaten')
@click.option('--kreis', help='Kreis code to import (e.g., DE-NW-05154)')
@with_appcontext
def import_geodaten(kreis):
    """Import geodata from unternehmensdaten.org API."""
    from .services import GeodatenService

    service = GeodatenService()

    if not service.is_configured:
        click.echo("Error: API key not configured.")
        click.echo("Set UNTERNEHMENSDATEN_API_KEY in plugin settings.")
        return

    if kreis:
        click.echo(f"Importing hierarchy for {kreis}...")
        try:
            result = service.import_kreis_hierarchy(kreis)
            click.echo(f"  Land: {result['land'].name}")
            click.echo(f"  Bundesland: {result['bundesland'].name}")
            click.echo(f"  Kreis: {result['kreis'].name}")

            click.echo("Importing Orte...")
            count = service.import_orte(result['kreis'].id)
            click.echo(f"  Imported {count} Orte")
        except Exception as e:
            click.echo(f"Error: {e}")
    else:
        click.echo("Importing all Länder...")
        try:
            count = service.import_laender()
            click.echo(f"Imported {count} Länder")
        except Exception as e:
            click.echo(f"Error: {e}")


@directory_cli.command('stats')
@with_appcontext
def stats():
    """Show directory statistics."""
    from .models import (
        DirectoryType,
        DirectoryEntry,
        GeoLand,
        GeoBundesland,
        GeoKreis,
        GeoOrt,
    )

    click.echo("=== Business Directory Statistics ===\n")

    click.echo("Directory Types:")
    types = DirectoryType.query.all()
    for t in types:
        active = t.entries.filter_by(active=True).count()
        total = t.entries.count()
        status = "✓" if t.active else "✗"
        click.echo(f"  [{status}] {t.name}: {active}/{total} entries")

    click.echo("\nGeodaten:")
    click.echo(f"  Länder: {GeoLand.query.count()}")
    click.echo(f"  Bundesländer: {GeoBundesland.query.count()}")
    click.echo(f"  Kreise: {GeoKreis.query.count()}")
    click.echo(f"  Orte: {GeoOrt.query.count()}")

    imported = GeoKreis.query.filter_by(orte_importiert=True).count()
    click.echo(f"  Kreise mit Orten: {imported}")

    click.echo("\nEntries:")
    total = DirectoryEntry.query.count()
    active = DirectoryEntry.query.filter_by(active=True).count()
    verified = DirectoryEntry.query.filter_by(verified=True).count()
    self_managed = DirectoryEntry.query.filter_by(self_managed=True).count()
    click.echo(f"  Total: {total}")
    click.echo(f"  Active: {active}")
    click.echo(f"  Verified: {verified}")
    click.echo(f"  Self-managed: {self_managed}")
