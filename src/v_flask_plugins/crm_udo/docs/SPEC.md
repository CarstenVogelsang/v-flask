# CRM UDO Plugin - Spezifikation

## Übersicht

Das CRM UDO Plugin bietet eine Admin-Oberfläche zur Verwaltung von Unternehmen, Organisationen und Kontakten. Es ist ein **API-Consumer** für die UDO API und speichert keine lokalen Daten.

## Entitäten

### Unternehmen (ComUnternehmen)

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| id | UUID | Ja | Primärschlüssel |
| kurzname | String | Ja | Kurze Bezeichnung |
| firmierung | String | Nein | Vollständiger Firmenname |
| strasse | String | Nein | Straßenname |
| strasse_hausnr | String | Nein | Hausnummer |
| geo_ort_id | UUID | Nein | FK zu GeoOrt |
| legacy_id | Integer | Nein | Migration |

### Kontakt (ComKontakt)

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| id | UUID | Ja | Primärschlüssel |
| unternehmen_id | UUID | Ja | FK zu Unternehmen |
| vorname | String | Ja | Vorname |
| nachname | String | Ja | Nachname |
| anrede | String | Nein | Herr/Frau/Divers |
| titel | String | Nein | Dr., Prof. etc. |
| position | String | Nein | Berufliche Position |
| abteilung | String | Nein | Abteilung |
| telefon | String | Nein | Telefonnummer |
| mobil | String | Nein | Mobilnummer |
| fax | String | Nein | Faxnummer |
| email | String | Nein | E-Mail-Adresse |
| notizen | Text | Nein | Freitext |
| ist_hauptkontakt | Boolean | Nein | Hauptansprechpartner |
| typ | String | Nein | Kontakttyp |

### Organisation (ComOrganisation)

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| id | UUID | Ja | Primärschlüssel |
| kurzname | String | Ja | Bezeichnung |
| legacy_id | Integer | Nein | Migration |

## User Stories

### POC (Proof of Concept)

- **US-001**: Als Admin kann ich alle Unternehmen sehen (Liste mit Pagination)
- **US-002**: Als Admin kann ich ein Unternehmen im Detail ansehen
- **US-003**: Als Admin kann ich ein neues Unternehmen anlegen
- **US-004**: Als Admin kann ich ein Unternehmen bearbeiten
- **US-005**: Als Admin kann ich ein Unternehmen löschen

### MVP (Minimum Viable Product)

- **US-010**: Als Admin kann ich Kontakte zu einem Unternehmen hinzufügen
- **US-011**: Als Admin kann ich Kontakte bearbeiten
- **US-012**: Als Admin kann ich Kontakte löschen
- **US-013**: Als Admin kann ich einen Kontakt als Hauptkontakt markieren
- **US-020**: Als Admin kann ich Orte über Cascading Dropdowns auswählen
- **US-021**: Als Admin kann ich Orte per Schnellsuche finden
- **US-030**: Als Admin kann ich nach Unternehmen suchen

### V1 (Production)

- **US-100**: Als Admin kann ich global nach Unternehmen, Kontakten suchen
- **US-101**: Als Admin sehe ich Bestätigungsdialoge vor dem Löschen
- **US-102**: Als Admin sehe ich Feedback-Toasts nach Aktionen

## Nicht-funktionale Anforderungen

1. **Keine lokalen Models**: Alle Daten kommen aus der UDO API
2. **Fehlerbehandlung**: API-Fehler werden benutzerfreundlich angezeigt
3. **CSRF-Schutz**: Alle Formulare sind gegen CSRF geschützt
4. **Berechtigungen**: Nur Admins (`admin.*`) haben Zugriff

## Abhängigkeiten

- UDO API muss erreichbar sein
- Host-App muss `UDO_API_BASE_URL` konfiguriert haben
- Session muss `udo_access_token` für Auth enthalten
