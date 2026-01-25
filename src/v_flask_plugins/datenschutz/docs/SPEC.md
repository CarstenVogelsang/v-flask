# Datenschutz Plugin - Spezifikation

## Übersicht

Das Datenschutz Plugin generiert eine DSGVO-konforme Datenschutzerklärung mit automatischer Diensterkennung, vordefinierten Textbausteinen und Versionierung für Compliance-Audits.

## Zielgruppe

- **Admins**: Konfiguration der Datenschutzerklärung
- **Compliance-Beauftragte**: Versionierung und Audit-Trail
- **Website-Besucher**: Information über Datenverarbeitung

## User Stories

- Als Admin möchte ich eine Datenschutzerklärung aus Bausteinen zusammenstellen, damit ich DSGVO-konform bin
- Als Admin möchte ich automatisch erkennen welche Dienste ich nutze, damit ich nichts vergesse
- Als Compliance-Beauftragter möchte ich Änderungen nachvollziehen können, für Audits
- Als Besucher möchte ich wissen wie meine Daten verarbeitet werden

## Funktionale Anforderungen

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | Datenschutzerklärung aus Bausteinen generieren | Must | POC |
| F2 | Admin-Editor mit Baustein-Auswahl | Must | POC |
| F3 | Automatische Diensterkennung | Must | MVP |
| F4 | Live-Vorschau im Admin | Must | MVP |
| F5 | Versionierung mit Timestamps | Should | MVP |
| F6 | Warnungen bei fehlenden Bausteinen | Should | V1 |
| F7 | Cookie-Banner Integration | Could | V2 |

## Bausteine-Kategorien

| Kategorie | Beispiele |
|-----------|-----------|
| Pflicht | Verantwortlicher, Betroffenenrechte, Aufsichtsbehörde |
| Server | Server-Logs, SSL/TLS, Hosting |
| Formulare | Kontaktformular, Newsletter |
| Analytics | Google Analytics, Matomo |
| Externe Medien | YouTube, Google Maps, Fonts |
| Social Media | Facebook, Instagram, Twitter |
| E-Commerce | Zahlungsanbieter, Shop-Funktionen |

## Automatische Erkennung

Das Plugin erkennt eingebundene Dienste durch:
- Aktivierte Plugins (z.B. kontakt → Kontaktformular-Baustein)
- Template-Analyse (z.B. eingebundene Scripts)
- Konfiguration (z.B. Analytics-Keys)

## Nicht-funktionale Anforderungen

- **Compliance**: Erfüllt DSGVO Art. 13/14
- **Nachvollziehbarkeit**: Änderungshistorie für Audits
- **Aktualität**: Bausteine werden gepflegt

## Abgrenzung (Out of Scope)

- Automatische Einwilligungsverwaltung (Consent Management)
- Erstellung von Verarbeitungsverzeichnissen
- Datenschutz-Folgenabschätzung
