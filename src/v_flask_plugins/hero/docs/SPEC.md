# Hero Plugin - Spezifikation

## Übersicht

Das Hero Plugin ermöglicht die Konfiguration und Anzeige von Hero Sections auf Landing Pages mit drei Layout-Varianten (Zentriert, Geteilt, Overlay), Text-Templates mit Jinja2-Platzhaltern und route-basierter Seitenzuweisung.

## Zielgruppe

- **Admins**: Konfiguration von Hero Sections im Backend
- **Marketing**: Erstellung von Landing-Page-Headern mit CTAs
- **Entwickler**: Integration in Templates via Context Processor

## User Stories

- Als Admin möchte ich Hero Sections mit verschiedenen Layouts erstellen, damit ich ansprechende Landing Pages gestalten kann
- Als Admin möchte ich Text-Templates mit Platzhaltern verwenden, damit ich dynamische Inhalte darstellen kann
- Als Admin möchte ich Hero Sections bestimmten Seiten zuweisen, damit unterschiedliche Seiten unterschiedliche Heroes haben
- Als Besucher möchte ich eine ansprechende Hero Section sehen, die mich zum CTA führt

## Funktionale Anforderungen

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | Drei Layout-Varianten: Centered, Split, Overlay | Must | POC |
| F2 | Text-Templates mit Jinja2-Platzhaltern | Must | POC |
| F3 | Media-Integration für Hintergrundbilder | Must | POC |
| F4 | Admin-UI mit Live-Vorschau | Must | MVP |
| F5 | Route-basierte Seitenzuweisung | Must | MVP |
| F6 | Multiple Slots (hero_top, above_content, below_content) | Should | MVP |
| F7 | Content-Slot-Provider Integration | Should | V1 |
| F8 | Prioritätssteuerung bei Konflikten | Should | V1 |

## Layout-Varianten

| Variante | Beschreibung |
|----------|--------------|
| `centered` | Text zentriert über dem Hintergrundbild |
| `split` | Bild links, Text rechts (50/50) |
| `overlay` | Vollbild mit dunklem Gradient-Overlay |

## Verfügbare Platzhalter

- `{{ betreiber.name }}` - Name des Betreibers
- `{{ plattform.name }}` - Plattformname
- `{{ ort.name }}` - Ortsname (aus Template-Kontext)

## Nicht-funktionale Anforderungen

- **Performance**: Hero-Rendering < 50ms
- **Sicherheit**: Nur Admin-Zugriff auf Konfiguration
- **Kompatibilität**: Media-Plugin erforderlich

## Abgrenzung (Out of Scope)

- Video-Hintergründe (ggf. spätere Erweiterung)
- A/B-Testing von Hero-Varianten
- Automatische Bildoptimierung (liegt beim Media-Plugin)
