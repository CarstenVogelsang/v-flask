# Fragebogen Plugin - Spezifikation

## Übersicht

Das Fragebogen-Plugin ist ein vollständiges Umfrage-System für v-flask Anwendungen mit:
- Mehrseitigen Wizard-Fragebögen (V2 Schema)
- Magic-Link System für Login-freie Teilnahme
- Flexibler Teilnehmerquellen-Konfiguration
- XLSX-Export der Ergebnisse

## Features

### Fragebogen-Erstellung
- Mehrseitiges Wizard-Format (V2 Schema)
- 11 Fragetypen: text, single_choice, multiple_choice, dropdown, skala, ja_nein, date, number, url, group, table
- Bedingte Anzeige (show_if)
- Vorausfüllung aus Teilnehmerdaten (prefill)
- Versionierung von Fragebögen

### Teilnahme
- Magic-Link Token für direkten Zugang
- Anonyme Teilnahme mit Kontaktdatenerfassung
- Auto-Save während des Ausfüllens
- Fortschritt über Sessions hinweg speichern

### Teilnehmerquellen
- Konfigurierbare Datenquellen (Kunde, Lead, Unternehmen, etc.)
- Flexibles Field-Mapping (email, name, anrede, titel)
- Begrüßungs-Templates mit Jinja2

### Export
- XLSX-Export aller Antworten
- Filteroptionen (nur abgeschlossene, mit Zeitstempeln)

## Datenmodell

### Fragebogen
```
id              INTEGER PRIMARY KEY
titel           VARCHAR(200) NOT NULL
beschreibung    TEXT
definition_json JSON NOT NULL
status          VARCHAR(20) ['entwurf', 'aktiv', 'geschlossen']
erlaubt_anonym  BOOLEAN
erstellt_von_id INTEGER FK(user.id)
vorgaenger_id   INTEGER FK(fragebogen.id)
version_nummer  INTEGER
archiviert      BOOLEAN
```

### FragebogenTeilnahme
```
id              INTEGER PRIMARY KEY
fragebogen_id   INTEGER FK(fragebogen.id)
teilnehmer_id   INTEGER (nullable)
teilnehmer_typ  VARCHAR(50) (nullable)
token           VARCHAR(64) UNIQUE
status          VARCHAR(20) ['eingeladen', 'gestartet', 'abgeschlossen']
kontakt_email   VARCHAR(255)
kontakt_name    VARCHAR(255)
```

### FragebogenAntwort
```
id            INTEGER PRIMARY KEY
teilnahme_id  INTEGER FK(fragebogen_teilnahme.id)
frage_id      VARCHAR(50)
antwort_json  JSON
```

### ParticipantSourceConfig
```
id                INTEGER PRIMARY KEY
model_path        VARCHAR(255) UNIQUE
display_name      VARCHAR(100)
field_mapping     JSON
greeting_template TEXT
query_filter      JSON
is_default        BOOLEAN
is_active         BOOLEAN
```

## V2 Schema Format

```json
{
  "version": 2,
  "seiten": [
    {
      "id": "s1",
      "titel": "Abschnitt 1",
      "hilfetext": "Optionaler Hilfetext",
      "fragen": [
        {
          "id": "q1",
          "typ": "text",
          "frage": "Ihre Frage?",
          "pflicht": true,
          "prefill": "teilnehmer.email",
          "hilfetext": "Hilfetext zur Frage",
          "show_if": {
            "frage_id": "q_vorherig",
            "equals": "ja"
          }
        }
      ]
    }
  ]
}
```

## Field-Mapping Format

```json
{
  "email": "email",
  "name": {
    "fields": ["vorname", "nachname"],
    "separator": " "
  },
  "anrede": "anrede",
  "titel": "titel"
}
```

## Admin-Routen

| Route | Beschreibung |
|-------|--------------|
| `/admin/fragebogen/` | Übersicht aller Fragebögen |
| `/admin/fragebogen/neu` | Neuen Fragebogen erstellen |
| `/admin/fragebogen/<id>` | Fragebogen-Details |
| `/admin/fragebogen/<id>/edit` | Fragebogen bearbeiten |
| `/admin/fragebogen/<id>/teilnehmer` | Teilnehmer verwalten |
| `/admin/fragebogen/<id>/auswertung` | Statistiken anzeigen |
| `/admin/fragebogen/<id>/export` | XLSX-Export |
| `/admin/fragebogen/participant-sources` | Teilnehmerquellen verwalten |

## Öffentliche Routen

| Route | Beschreibung |
|-------|--------------|
| `/fragebogen/<token>` | Wizard-Ansicht für Teilnehmer |
| `/fragebogen/<token>/danke` | Danke-Seite nach Abschluss |
