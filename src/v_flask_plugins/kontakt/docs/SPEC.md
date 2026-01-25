# Kontakt Plugin - Spezifikation

## Übersicht

Das Kontakt Plugin stellt ein öffentliches Kontaktformular und einen Admin-Bereich zur Verwaltung eingehender Anfragen bereit, inklusive Lese-Status-Tracking und optionaler E-Mail-Benachrichtigung.

## Zielgruppe

- **Besucher**: Kontaktaufnahme über Formular
- **Admins**: Verwaltung und Beantwortung von Anfragen

## User Stories

- Als Besucher möchte ich ein Kontaktformular ausfüllen, damit ich eine Anfrage senden kann
- Als Admin möchte ich alle Kontaktanfragen einsehen, damit ich diese bearbeiten kann
- Als Admin möchte ich sehen welche Anfragen neu sind, damit ich priorisieren kann
- Als Admin möchte ich per E-Mail benachrichtigt werden, wenn neue Anfragen eingehen

## Funktionale Anforderungen

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | Öffentliches Kontaktformular | Must | POC |
| F2 | Speicherung in Datenbank | Must | POC |
| F3 | Admin-Liste aller Anfragen | Must | MVP |
| F4 | Lese-Status (gelesen/ungelesen) | Must | MVP |
| F5 | Badge für ungelesene Anfragen | Should | MVP |
| F6 | E-Mail-Benachrichtigung | Should | V1 |
| F7 | Telefon als optionales Feld | Should | V1 |

## Formularfelder

| Feld | Pflicht | Validierung |
|------|---------|-------------|
| Name | Ja | Max. 100 Zeichen |
| E-Mail | Ja | E-Mail-Format |
| Telefon | Konfigurierbar | Optional |
| Nachricht | Ja | Min. 10 Zeichen |

## Nicht-funktionale Anforderungen

- **Sicherheit**: CSRF-Schutz, Server-seitige Validierung
- **Usability**: Erfolgsmeldung nach Absenden
- **Accessibility**: Formular-Labels korrekt verknüpft

## Abgrenzung (Out of Scope)

- Spam-Schutz (Captcha) - sollte auf App-Ebene integriert werden
- Ticket-System mit Zuweisungen
- Automatische Antworten
