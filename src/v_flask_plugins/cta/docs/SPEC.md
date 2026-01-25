# CTA Plugin - Spezifikation

## Übersicht

Das CTA (Call-to-Action) Plugin ermöglicht die Erstellung und Platzierung von CTA-Sections mit drei Design-Varianten (Card, Alert, Floating), Text-Templates mit Jinja2-Platzhaltern und route-basierter Seitenzuweisung.

## Zielgruppe

- **Admins**: Konfiguration von CTA Sections im Backend
- **Marketing**: Erstellung von Conversion-optimierten CTAs
- **Entwickler**: Integration in Templates via Content-Slots

## User Stories

- Als Admin möchte ich CTA Sections mit verschiedenen Designs erstellen, damit ich Besucher zu Aktionen motivieren kann
- Als Admin möchte ich CTAs bestimmten Seiten zuweisen, damit ich zielgerichtete Aufrufe platzieren kann
- Als Marketing möchte ich dynamische Platzhalter nutzen, damit CTAs personalisiert wirken
- Als Besucher möchte ich klare Handlungsaufforderungen sehen, die mich zum nächsten Schritt leiten

## Funktionale Anforderungen

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | Drei Design-Varianten: Card, Alert, Floating | Must | POC |
| F2 | Text-Templates mit Jinja2-Platzhaltern | Must | POC |
| F3 | Admin-UI mit Live-Vorschau | Must | MVP |
| F4 | Route-basierte Seitenzuweisung | Must | MVP |
| F5 | Content-Slot-Provider Integration | Must | V1 |
| F6 | Prioritätssteuerung bei Konflikten | Should | V1 |
| F7 | Multiple CTAs pro Seite (verschiedene Slots) | Should | V1 |

## Design-Varianten

| Variante | Beschreibung | Typischer Einsatz |
|----------|--------------|-------------------|
| `card` | Box mit Hintergrund, Titel, Text, Button | Am Ende von Artikeln |
| `alert` | Schmale Leiste mit Hinweis-Charakter | Unter Navigation |
| `floating` | Schwebendes Element am Rand | Permanenter Aufruf |

## Verfügbare Platzhalter

- `{{ plattform.name }}` - Plattformname (aus Plugin-Settings)
- `{{ plattform.zielgruppe }}` - Zielgruppe (aus Plugin-Settings)
- `{{ location.bezeichnung }}` - Location-Bezeichnung
- `{{ ort.name }}` - Ortsname (aus Template-Kontext)
- `{{ kreis.name }}` - Kreisname (aus Template-Kontext)
- `{{ bundesland.name }}` - Bundeslandname (aus Template-Kontext)

## Nicht-funktionale Anforderungen

- **Performance**: CTA-Rendering < 20ms
- **Sicherheit**: Nur Admin-Zugriff auf Konfiguration
- **Accessibility**: CTAs müssen Screenreader-freundlich sein

## Abgrenzung (Out of Scope)

- Tracking/Analytics (sollte via separate Integration erfolgen)
- A/B-Testing von CTA-Varianten
- Popup-CTAs mit Timing/Scroll-Trigger
