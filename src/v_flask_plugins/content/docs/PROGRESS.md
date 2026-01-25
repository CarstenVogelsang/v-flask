# Content Plugin - Fortschritt

## Aktuelle Phase: MVP

## Phasen-Übersicht

### Phase 1: POC (Proof of Concept)
**Ziel:** Grundfunktion nachweisen

- [x] Plugin-Struktur erstellt
- [x] PluginManifest definiert
- [x] Basis-Models (ContentBlock, ContentAssignment, TextSnippet)
- [x] Admin-Blueprint registriert

**Status:** ✅ Abgeschlossen

### Phase 2: MVP (Minimum Viable Product)
**Ziel:** Nutzbar für erste User

- [x] 4 Basis-Intentionen definiert
- [x] 4 Basis-Layouts definiert
- [x] 3-Schritte-Wizard implementiert
- [x] Admin-Liste mit CRUD
- [x] Seitenzuweisung über Slots
- [x] ContentSlotProvider implementiert
- [x] Rendering-Templates für alle Layouts
- [x] Textbaustein-System (System + User)
- [x] ~20 vordefinierte Textbausteine
- [x] Branchenspezifische Snippets (Gastronomie, Einzelhandel)
- [x] CSRF-Schutz in allen Formularen
- [x] Dokumentation (SPEC, TECH, PROGRESS)

**Status:** ✅ Abgeschlossen

### Phase 3: V1 (Erste Release-Version)
**Ziel:** Production-ready

- [ ] Medienbibliothek-Picker Integration (aktuell Prompt-Workaround)
- [ ] Vorschau im Admin
- [ ] Drag & Drop Sortierung
- [ ] Error Handling verbessern
- [ ] Unit Tests
- [ ] Performance-Optimierung (Caching)

**Status:** 🟡 In Arbeit

### Phase 4: V2 (Erweiterte Features)
**Ziel:** Erweiterte Funktionalität

- [ ] KI-Integration via OpenRouter-Service
- [ ] Mehr Branchen-Vorlagen
- [ ] Erweiterte Layouts (Galerie, Cards)
- [ ] Multi-Language Support
- [ ] Versions-History für Bausteine

**Status:** ⚪ Nicht begonnen

---

## Changelog

### 2026-01-25 - MVP implementiert

- ✅ Plugin-Grundstruktur angelegt
- ✅ Models: ContentBlock, ContentAssignment, TextSnippet
- ✅ Services: ContentService, SnippetService
- ✅ ContentSlotProvider für Slot-System
- ✅ Admin-Routes mit 3-Schritte-Wizard
- ✅ Admin-Templates (DaisyUI):
  - Liste aller Bausteine
  - Wizard Step 1-3
  - Bearbeiten
  - Seitenzuweisung
  - Textbausteine-Verwaltung
- ✅ Layout-Templates:
  - banner_text.html
  - bild_links.html
  - bild_rechts.html
  - nur_text.html
- ✅ Daten-Dateien:
  - intentions.json (4 Intentionen)
  - layouts.json (4 Layouts)
  - Snippets: allgemein (startseite, ueber_uns, leistungen, team)
  - Snippets: branchen (gastronomie, einzelhandel)
- ✅ Marketplace-Eintrag vorbereitet
- ✅ Dokumentation komplett

## Bekannte Einschränkungen

1. **Medienbibliothek:** Aktuell nur über manuelles Eingeben der Media-ID. Echte Picker-Integration folgt in V1.
2. **Vorschau:** Keine Live-Vorschau im Admin. Bausteine müssen auf echten Seiten getestet werden.
3. **Sortierung:** Bei mehreren Bausteinen auf einer Seite nur über sort_order in DB steuerbar.

## Nächste Schritte

1. Plugin im Test-Projekt aktivieren und testen
2. Media-Picker-Modal implementieren
3. Admin-Vorschau hinzufügen
