# Business Directory Plugin - Fortschritt

## Status: In Entwicklung (v0.1.0-alpha)

## Erledigte Aufgaben

### Phase 1: Grundstruktur ✅
- [x] Plugin-Manifest (`__init__.py`)
- [x] Model-Struktur

### Phase 2: Models ✅
- [x] DirectoryType (Multi-Directory Schema)
- [x] DirectoryEntry (generischer Eintrag)
- [x] GeoLand
- [x] GeoBundesland
- [x] GeoKreis
- [x] GeoOrt
- [x] RegistrationDraft
- [x] ClaimRequest

### Phase 3: Routes ✅
- [x] Admin Routes (Entries)
- [x] Admin Routes (Types)
- [x] Admin Routes (Geodaten)
- [x] Public Routes (Geo-Drilling)
- [x] Register Routes (Self-Registration)
- [x] Provider Routes (Dashboard)
- [x] API Routes (Search, Autocomplete)

### Phase 4: Services ✅
- [x] GeodatenService (unternehmensdaten.org API)
- [x] EntryService (Business Logic)

### Phase 5: Templates (Teilweise) 🟡
- [x] Admin Types List
- [x] Admin Types Form
- [x] Admin Dashboard
- [x] Public Index
- [x] Public Type Index
- [ ] Admin Entries List
- [ ] Admin Entries Form
- [ ] Admin Geodaten Views
- [ ] Admin Review Queue
- [ ] Public Bundesland/Kreis/Ort Views
- [ ] Public Entry Detail
- [ ] Register Wizard Steps
- [ ] Provider Dashboard

### Phase 6: Dokumentation ✅
- [x] SPEC.md
- [x] TECH.md
- [x] PROGRESS.md

## Offene Aufgaben

### Templates (Priorität: Hoch)
- [ ] Vollständige Template-Implementierung für alle Views
- [ ] Dynamische Feldanzeige basierend auf field_schema
- [ ] HTMX-Integration für interaktive Features

### Testing (Priorität: Mittel)
- [ ] Unit-Tests für Services
- [ ] Integration-Tests für Routes
- [ ] E2E-Tests mit Playwright

### Features (Priorität: Mittel)
- [ ] Kartenansicht (optional)
- [ ] Bild-Upload (Media-Plugin Integration)
- [ ] E-Mail-Benachrichtigungen

### Optimierung (Priorität: Niedrig)
- [ ] Caching für häufige Abfragen
- [ ] Suchindex-Integration
- [ ] Performance-Optimierung für große Datenmengen

## Bekannte Probleme

1. **Templates unvollständig**: Nicht alle Views haben Templates. Fehlende Templates führen zu 500-Fehlern.

2. **Keine Migrations**: Plugin hat noch keine eigenen Alembic-Migrations. Diese müssen in der Host-App generiert werden.

## Nächste Schritte

1. Testprojekt `vz_spielwaren` erstellen
2. Plugin dort installieren und testen
3. Fehlende Templates implementieren
4. Migration erstellen und testen
5. In vz_fruehstueckenclick integrieren

## Changelog

### v0.1.0-alpha (2026-01-23)
- Initial Plugin-Struktur
- Alle Core-Models implementiert
- Alle Routes definiert
- Services für Geodaten und Entries
- Basis-Templates für Admin und Public
- Dokumentation erstellt
