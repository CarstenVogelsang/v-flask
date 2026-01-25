# Business Directory Plugin - Spezifikation

## Übersicht

Das **business_directory** Plugin bietet ein vollständiges Verzeichnissystem für lokale Unternehmen mit:
- Multi-Directory-Unterstützung (mehrere Verzeichnistypen pro Projekt)
- Geo-Drilling Navigation (Land → Bundesland → Kreis → Ort → Eintrag)
- Self-Registration Wizard für Betreiber
- Ownership-Claiming für bestehende Einträge
- Admin-Konfiguration über UI (keine Hardcodierung)

## Anwendungsfälle

### Beispiel 1: Frühstücks-Verzeichnis
- Ein Verzeichnistyp: "Frühstückslokale"
- Felder: Öffnungszeiten, Preise, Reservierung erforderlich

### Beispiel 2: Spielwaren-Portal
- Zwei Verzeichnistypen: "Händler" + "Hersteller"
- Händler-Felder: Öffnungszeiten, geführte Marken, Parkplätze
- Hersteller-Felder: Marken, Gründungsjahr, Mitarbeiterzahl

## Datenmodell

### DirectoryType
Definiert einen Verzeichnistyp (z.B. "Händler"):
- `slug`: URL-Bezeichner (z.B. "haendler")
- `name`: Anzeigename
- `field_schema`: JSON mit Felddefinitionen
- `registration_steps`: JSON mit Wizard-Konfiguration
- `display_config`: JSON mit Anzeige-Konfiguration

### DirectoryEntry
Der eigentliche Verzeichniseintrag:
- Feste Basisfelder: name, strasse, telefon, email, website
- `data`: JSON mit typenspezifischen Feldern
- `geo_ort_id`: Verknüpfung zur Geo-Hierarchie
- `owner_id`: Eigentümer (User)

### Geo-Hierarchie
- **GeoLand**: DE, AT, CH
- **GeoBundesland**: NRW, Bayern, etc.
- **GeoKreis**: Kreise und kreisfreie Städte
- **GeoOrt**: Orte mit PLZ

## URL-Struktur

```
/                                   # Plugin-Startseite
/<type>/                            # Typ-Übersicht (Bundesländer)
/<type>/<bundesland>/               # Bundesland (Kreise)
/<type>/<bundesland>/<kreis>/       # Kreis (Orte)
/<type>/<bundesland>/<kreis>/<ort>/ # Ort (Einträge)
/<type>/.../<ort>/<entry>/          # Eintrag-Detail
/<type>/search?q=...                # Suche
```

## Admin-Funktionen

### Verzeichnistypen verwalten
- CRUD für DirectoryType
- Feld-Schema Editor (JSON)
- Registrierungs-Schritte konfigurieren
- Anzeige-Konfiguration

### Einträge verwalten
- Liste mit Filterung nach Typ, Status
- Detailbearbeitung mit dynamischen Feldern
- Aktivieren/Deaktivieren
- Review-Queue für neue Einträge

### Geodaten verwalten
- Import aus unternehmensdaten.org API
- Hierarchische Ansicht
- Bulk-Import für Bundesländer

## Self-Registration

1. **Verzeichnistyp wählen**: Welches Verzeichnis?
2. **Account-Daten**: E-Mail, Passwort
3. **Grunddaten**: Name, Beschreibung
4. **Adresse**: Straße, PLZ, Ort
5. **Kontakt**: Telefon, Website
6. **Typ-spezifische Felder**: Aus field_schema
7. **Zusammenfassung**: Prüfen und absenden

## Claiming

Bestehende Einträge können von Eigentümern übernommen werden:
1. Eintrag suchen
2. Nachweis auswählen (Impressum, Social Media, etc.)
3. URL/Beschreibung eingeben
4. Admin prüft und genehmigt

## Berechtigungen

| Permission | Beschreibung |
|-----------|--------------|
| `business_directory.read` | Einträge anzeigen |
| `business_directory.create` | Einträge erstellen |
| `business_directory.update` | Einträge bearbeiten |
| `business_directory.delete` | Einträge löschen |
| `admin.*` | Typen und Geodaten verwalten |

## Konfiguration

### Plugin-Einstellungen
- `unternehmensdaten_api_key`: API-Key für Geodaten-Import
- `geoapify_api_key`: Optional für Business-Suche

### Feld-Schema Beispiel
```json
{
  "oeffnungszeiten": {
    "type": "opening_hours",
    "label": "Öffnungszeiten",
    "required": true,
    "show_in_detail": true
  },
  "marken": {
    "type": "multi_select",
    "label": "Geführte Marken",
    "required": false
  }
}
```

## Abhängigkeiten

- v-flask core (User, Permission, Betreiber)
- Flask-Login (Session-Management)
- Slugify (URL-Generierung)
- Requests + Tenacity (API-Calls mit Retry)
