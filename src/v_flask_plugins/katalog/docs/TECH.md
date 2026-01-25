# Katalog Plugin - Technische Dokumentation

## Architektur-Übersicht

```
katalog/
├── __init__.py          # KatalogPlugin Manifest
├── models.py            # KatalogKategorie, KatalogPDF
├── routes/
│   ├── public.py        # Öffentliche Katalog-Ansicht
│   └── admin.py         # Admin-Verwaltung
├── services/
│   └── pdf_service.py   # PDF-Handling, Cover-Generierung
└── templates/
    └── katalog/
        ├── public/      # Katalog-Liste, PDF-Viewer
        └── admin/       # Upload, Verwaltung
```

## Komponenten

### Models

| Model | Tabelle | Beschreibung |
|-------|---------|--------------|
| `KatalogKategorie` | `katalog_kategorie` | Kategorien für PDFs |
| `KatalogPDF` | `katalog_pdf` | Hochgeladene PDF-Dateien |

### Routes

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/katalog/` | GET | Public | Katalog-Übersicht |
| `/katalog/<id>` | GET | Public | PDF-Viewer |
| `/katalog/<id>/download` | GET | Public/Auth | PDF-Download |
| `/admin/katalog/` | GET | Admin | Verwaltungs-Liste |
| `/admin/katalog/upload` | POST | Admin | PDF hochladen |
| `/admin/katalog/<id>` | GET/POST | Admin | PDF bearbeiten |
| `/admin/katalog/<id>/delete` | POST | Admin | PDF löschen |

### Services

| Service | Methode | Beschreibung |
|---------|---------|--------------|
| `pdf_service.upload(file)` | PDF speichern |
| `pdf_service.increment_views(id)` | View-Counter erhöhen |
| `pdf_service.increment_downloads(id)` | Download-Counter erhöhen |
| `pdf_service.generate_cover(pdf_path)` | Cover-Bild erzeugen |

## UI-Slots

| Slot | Konfiguration |
|------|---------------|
| `navbar_items` | `{label: 'Kataloge', url: 'katalog.index'}` |
| `footer_links` | `{label: 'PDF-Kataloge', url: 'katalog.index'}` |
| `admin_menu` | `{label: 'Kataloge', url: 'katalog_admin.list_pdfs'}` |
| `admin_dashboard_widgets` | Widget für Katalog-Verwaltung |

## Settings-Schema

| Key | Type | Default | Beschreibung |
|-----|------|---------|--------------|
| `upload_path` | string | `katalog/pdfs` | Upload-Verzeichnis |
| `max_file_size_mb` | int | 50 | Max. Dateigröße |
| `require_login` | bool | false | Login für Download |
| `show_view_count` | bool | false | Views anzeigen |
| `show_download_count` | bool | false | Downloads anzeigen |

## Abhängigkeiten

- **v_flask Core**: Auth, DB
- **PDF.js**: Client-seitiger PDF-Viewer (CDN)
- **PyMuPDF/pdf2image**: Optional für Cover-Generierung

## Datenbank-Schema

```sql
CREATE TABLE katalog_kategorie (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    sortierung INTEGER DEFAULT 0,
    aktiv BOOLEAN DEFAULT TRUE
);

CREATE TABLE katalog_pdf (
    id INTEGER PRIMARY KEY,
    titel VARCHAR(200) NOT NULL,
    beschreibung TEXT,
    dateiname VARCHAR(255) NOT NULL,
    dateipfad VARCHAR(500) NOT NULL,
    kategorie_id INTEGER REFERENCES katalog_kategorie(id),
    cover_pfad VARCHAR(500),
    view_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    aktiv BOOLEAN DEFAULT TRUE,
    erstellt_am DATETIME,
    aktualisiert_am DATETIME
);
```

## Technische Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| PDF.js via CDN | Kein Server-seitiges Rendering nötig |
| Counter in DB | Einfache Implementierung, ausreichend für kleine Mengen |
| Cover-Generierung optional | Nicht jeder Server hat ImageMagick/Poppler |
