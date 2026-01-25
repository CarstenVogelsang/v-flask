# Content Plugin - Spezifikation

## Übersicht

Das Content-Plugin bietet ein template-basiertes Content-System für allgemeine Seitenbereiche. Endkunden kennen es als "Inhaltsbausteine" oder einfach "Bausteine".

**Kernkonzept:** KEIN Rich-Text-Editor, sondern ein geführter Wizard:
1. Intention wählen → "Über uns", "Leistungen", "Team vorstellen"
2. Layout-Vorlage wählen → "Bild links + Text", "Banner + Text", etc.
3. Inhalte einfügen → Bilder aus Medienbibliothek, Texte aus Vorlagen
4. Seite zuweisen → Slot auf PageRoute auswählen

## Zielgruppe

- **Endkunden (Betreiber):** Erstellen und verwalten Inhaltsbausteine ohne HTML-Kenntnisse
- **Administratoren:** Verwalten Textbausteine und System-Vorlagen

## User Stories

### Endkunde

- Als Endkunde möchte ich einen "Über uns"-Bereich erstellen, damit Besucher mein Unternehmen kennenlernen.
- Als Endkunde möchte ich zwischen verschiedenen Layouts wählen können (Bild links/rechts, Banner), damit der Inhalt optisch ansprechend ist.
- Als Endkunde möchte ich vorgefertigte Texte als Vorlage nutzen, damit ich schneller starten kann.
- Als Endkunde möchte ich einen Baustein mehreren Seiten zuweisen, damit ich Inhalte wiederverwenden kann.

### Administrator

- Als Admin möchte ich branchenspezifische Textbausteine bereitstellen, damit Kunden passende Vorlagen finden.
- Als Admin möchte ich eigene Textbausteine erstellen, die global verfügbar sind.

## Funktionale Anforderungen

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | 4 Basis-Intentionen (Über uns, Leistungen, Team, Frei) | Must | MVP |
| F2 | 4 Basis-Layouts (Banner+Text, Bild links, Bild rechts, Nur Text) | Must | MVP |
| F3 | 3-Schritte-Wizard für Bausteine | Must | MVP |
| F4 | Medienbibliothek-Integration für Bilder | Must | MVP |
| F5 | Textbaustein-System (System + Benutzer) | Must | MVP |
| F6 | Seitenzuweisung über Slots | Must | MVP |
| F7 | ~20 vordefinierte Textbausteine | Should | MVP |
| F8 | Branchen-Filter für Textbausteine | Should | MVP |
| F9 | KI-generierte Textvorschläge | Could | V1 |
| F10 | Erweiterte Layouts (Galerie, Cards) | Could | V1 |

## Nicht-funktionale Anforderungen

- **Performance:** Slot-Rendering < 50ms
- **Sicherheit:** Nur Admin-Zugriff auf Verwaltung
- **Usability:** Wizard-basierter Workflow für einfache Bedienung

## Abgrenzung (Out of Scope)

- WYSIWYG-Editor (bewusste Entscheidung für Template-System)
- Spezialisierte Inhalte wie Öffnungszeiten, Preislisten (eigene Plugins)
- Multi-Language Support (V2)
- Drag & Drop Reihenfolge (V1)
