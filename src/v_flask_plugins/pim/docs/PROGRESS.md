# PIM Plugin - Fortschritt & Phasenplan

## Versionierung

| Version | Beschreibung |
|---------|--------------|
| **MVP** | Minimale funktionsfähige Version |
| **V0** | Beta-Version (Feature-Complete für MVP-Scope) |
| **V1** | Erste stabile Version + Varianten + Mehrsprachigkeit + S3 |
| **V2+** | Weitere Iterationen |

---

## MVP - Minimalfunktionen

### Ziele
- Produkte CRUD mit Bildern
- Hierarchische Kategorien
- Steuersätze
- Barcode-Handling (GTIN/EAN/UPC)
- CSV-Import/Export
- Services für Shop-Plugin bereitstellen

### Tasks

#### 1. Grundstruktur

| Task | Status | Beschreibung |
|------|--------|--------------|
| Plugin-Skelett | ✅ | `pim/` mit __init__.py |
| Models definieren | ✅ | Product, Category, TaxRate, ProductImage, Manufacturer, Brand, Series, ProductGroup, PriceTag |
| Repository-Interfaces | ⬜ | Abstrakte Basis-Klassen |
| PostgreSQL-Repos | ⬜ | Implementierung für PostgreSQL |
| Migrationen | ⬜ | Alembic-Skripte für alle Tabellen |

#### 2. Services

| Task | Status | Beschreibung |
|------|--------|--------------|
| ProductService | ✅ | CRUD + Suche + Barcode-Lookup |
| CategoryService | ✅ | Baumstruktur + Breadcrumbs |
| ImageService | ⬜ | Upload + Thumbnails + Sortierung |
| BarcodeService | ✅ | Auto-Erkennung + Validierung (Modulo-10) |
| ImportService | ⬜ | CSV-Import mit Validierung |
| ExportService | ⬜ | CSV-Export |
| ManufacturerService | ✅ | CRUD für Hersteller/Marken/Serien |
| ProductGroupService | ✅ | CRUD für Warengruppen |
| PriceTagService | ✅ | CRUD für Preis-Tags |
| TaxRateService | ✅ | CRUD für Steuersätze |

#### 3. API

| Task | Status | Beschreibung |
|------|--------|--------------|
| Pydantic-Schemas | ⬜ | Request/Response-Modelle |
| Product-Endpoints | ⬜ | GET, POST, PUT, DELETE |
| Category-Endpoints | ⬜ | GET, POST, PUT, DELETE, Reorder |
| TaxRate-Endpoints | ⬜ | GET, POST, PUT, DELETE |
| Image-Endpoints | ⬜ | Upload, Delete, Reorder |
| Import/Export | ⬜ | POST /import, GET /export |
| Cascading Dropdown API | ✅ | Brands/Series für HTMX |
| Barcode Validation API | ✅ | GTIN/EAN/UPC Validierung |

#### 4. Admin UI

| Task | Status | Beschreibung |
|------|--------|--------------|
| Produkt-Liste | ✅ | Tabelle mit Suche, Filter |
| Produkt-Formular | ✅ | Anlegen/Bearbeiten mit Validierung |
| Bild-Upload | ⬜ | Drag & Drop, Sortierung, Hauptbild |
| Kategorie-Liste | ✅ | Hierarchie-Ansicht (Baum) |
| Kategorie-Formular | ✅ | Anlegen/Bearbeiten |
| Steuersatz-Liste | ✅ | Tabelle mit Standard-Markierung |
| Steuersatz-Formular | ✅ | Anlegen/Bearbeiten |
| Hersteller-Liste | ✅ | Accordion mit Marken |
| Hersteller-Formular | ✅ | Anlegen/Bearbeiten |
| Import-Dialog | ⬜ | CSV-Upload mit Vorschau |

#### 5. Bilder-Storage

| Task | Status | Beschreibung |
|------|--------|--------------|
| Storage-Abstraktion | ⬜ | ImageStorage ABC |
| LocalImageStorage | ⬜ | Lokale Dateispeicherung |
| Thumbnail-Generator | ⬜ | Automatische Größenanpassung |

---

## V0 (Beta) - Stabilisierung

### Ziele
- Alle MVP-Features stabil
- Vollständige Test-Abdeckung
- Dokumentation
- Bug-Fixes aus MVP-Testing

### Tasks

| Task | Status | Beschreibung |
|------|--------|--------------|
| Unit-Tests Services | ⬜ | ProductService, CategoryService, etc. |
| Integration-Tests API | ⬜ | Alle Endpoints |
| Admin UI Tests | ⬜ | Grundlegende UI-Tests |
| API-Dokumentation | ⬜ | OpenAPI/Swagger |
| Entwickler-Doku | ⬜ | Integration Guide für andere Plugins |
| Performance-Tests | ⬜ | 10.000 Produkte |
| Bug-Fixes | ⬜ | Aus internem Testing |

---

## V1 - Erweiterungen

### 1. Produktvarianten

| Task | Status | Beschreibung |
|------|--------|--------------|
| Varianten-Models | ⬜ | VariantAttribute, VariantValue |
| Migrationen | ⬜ | Neue Tabellen |
| VariantService | ⬜ | Matrix-Generierung, CRUD |
| Parent/Child-Logik | ⬜ | is_parent, parent_id in Product |
| Admin UI Varianten | ⬜ | Attribute definieren, Matrix-Editor |
| API Varianten | ⬜ | Endpoints für Varianten |

### 2. Mehrsprachigkeit (Produkttexte)

| Task | Status | Beschreibung |
|------|--------|--------------|
| Translation-Models | ⬜ | ProductTranslation, CategoryTranslation |
| Language-Model | ⬜ | pim_language Tabelle |
| Migrationen | ⬜ | Neue Tabellen |
| TranslationService | ⬜ | Fallback-Logik |
| Admin UI i18n | ⬜ | Tabs pro Sprache im Formular |
| API i18n | ⬜ | ?lang=de Query-Parameter |

### 3. S3 Bilder-Storage

| Task | Status | Beschreibung |
|------|--------|--------------|
| S3ImageStorage | ⬜ | boto3-Implementierung |
| Einstellungs-UI | ⬜ | Storage-Typ wählen |
| Migration bestehend | ⬜ | Tool: Lokal → S3 migrieren |
| CDN-Integration | ⬜ | Optionale CDN-URL |

---

## V2+ - Zukunft (Ideen)

| Feature | Beschreibung |
|---------|--------------|
| Attribute-System | Freie Attribute (nicht nur Varianten) |
| Bundles | Produkt-Pakete mit Rabatt |
| Cross-Selling | "Kunden kauften auch" |
| Bulk-Editor | Massenbearbeitung in Tabelle |
| Bilder-KI | Auto-Tagging, Hintergrund entfernen |
| Firebird-Repository | Legacy-DB-Anbindung |

---

## Changelog

### 2026-01-21 - POC Phase 1 implementiert

#### Added
- ✅ SPEC.md erstellt mit User Stories
- ✅ TECH.md erstellt mit Architektur und Datenmodell
- ✅ PROGRESS.md erstellt mit Phasenplan
- ✅ Plugin-Manifest (`__init__.py`) mit UI-Slots und Settings-Schema
- ✅ Models: Product, Category, TaxRate, ProductImage, Manufacturer, Brand, Series, ProductGroup, PriceTag
- ✅ Services: ProductService, CategoryService, TaxRateService, ManufacturerService, BarcodeService, ProductGroupService, PriceTagService
- ✅ Admin-Routes für Produkte, Kategorien, Steuersätze, Hersteller
- ✅ Admin-Templates (DaisyUI): Listen und Formulare
- ✅ API-Endpoints für kaskadierende Dropdowns (Marken/Serien)
- ✅ Barcode-Validierung API (GTIN/EAN/UPC)
- ✅ Plugin in plugins_marketplace.json eingetragen

#### Architektur-Entscheidungen
- Varianten vorbereitet: `is_parent`, `parent_id` in Product-Model
- Mehrsprachigkeit vorbereitet: Separate Translation-Tabellen (nicht JSON)
- Bilder-Storage abstrahiert für spätere S3-Integration
- Barcode-Service mit Modulo-10 Prüfsummen-Validierung (GTIN-8/12/13/14)
- UUID als Primary Keys für bessere Verteilung
- Soft-Delete via `is_active` Flag

#### Offene Punkte
- [ ] Datenbank-Migrationen erstellen
- [ ] Bilder-Upload integrieren (via Media-Plugin)
- [ ] CSV-Import/Export implementieren
- [ ] Shop-Plugin wartet auf PIM
- [ ] CRM-Plugin ebenfalls erforderlich für Shop

---

## Abhängigkeiten

```
                    ┌─────────────┐
                    │    Core     │
                    │  (v-flask)  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │   PIM   │  │   CRM   │  │  ...    │
        └────┬────┘  └────┬────┘  └─────────┘
             │            │
             └──────┬─────┘
                    │
                    ▼
              ┌─────────┐
              │  Shop   │
              │ (B2B)   │
              └─────────┘
```

**Reihenfolge der Implementierung:**
1. **PIM** (dieses Plugin) - keine Abhängigkeiten
2. **CRM** - keine Abhängigkeiten (parallel möglich)
3. **Shop** - benötigt PIM + CRM
