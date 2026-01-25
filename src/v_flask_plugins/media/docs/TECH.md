# Media Plugin - Technische Dokumentation

## Architektur-Übersicht

```
media/
├── __init__.py              # MediaPlugin Manifest, Context Processor
├── models.py                # Media Model mit Enums
├── routes.py                # Admin Blueprint (12KB)
├── services/
│   ├── media_service.py     # Upload, Resize, Picker-Rendering
│   ├── pexels_service.py    # Pexels API Integration
│   └── unsplash_service.py  # Unsplash API Integration
└── templates/
    └── media/
        ├── admin/           # Bibliotheksansicht, Upload
        └── components/      # Media Picker Komponente
```

## Komponenten

### Models

| Model | Tabelle | Beschreibung |
|-------|---------|--------------|
| `Media` | `media` | Hochgeladene Dateien mit Metadaten |
| `MediaType` | (Enum) | image, document, other |
| `MediaSource` | (Enum) | upload, pexels, unsplash |

### Routes

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/admin/media/` | GET | Admin | Bibliotheksansicht |
| `/admin/media/upload` | POST | Admin | Datei hochladen |
| `/admin/media/<id>` | GET/POST | Admin | Metadaten bearbeiten |
| `/admin/media/<id>/delete` | POST | Admin | Datei löschen |
| `/admin/media/search/pexels` | GET | Admin | Pexels Suche |
| `/admin/media/search/unsplash` | GET | Admin | Unsplash Suche |
| `/admin/media/import/<source>` | POST | Admin | Stock-Foto importieren |
| `/media/<path:filename>` | GET | Public | Datei ausliefern |

### Services

| Service | Methode | Beschreibung |
|---------|---------|--------------|
| `media_service.upload(file)` | Datei speichern und resizen |
| `media_service.get_url(id, size)` | URL für Größenvariante |
| `media_service.render_picker_component()` | HTML für Media Picker |
| `media_service.get_media(id)` | Media-Objekt abrufen |
| `pexels_service.search(query)` | Pexels API Suche |
| `unsplash_service.search(query)` | Unsplash API Suche |

### Templates

| Template | Zweck |
|----------|-------|
| `media/admin/library.html` | Bibliotheksübersicht mit Grid |
| `media/admin/edit.html` | Metadaten-Editor |
| `media/components/picker.html` | Media Picker Komponente |

## Context Processor

Das Plugin registriert Template-Funktionen:

```jinja2
{# Media Picker in Formularen #}
{{ get_media_picker_html('field_name', current_media_id) }}

{# URL für bestimmte Größe #}
<img src="{{ get_media_url(media_id, 'medium') }}">

{# Media-Objekt für weitere Verarbeitung #}
{% set media = get_media(media_id) %}
{% if media %}{{ media.attribution_html|safe }}{% endif %}
```

## UI-Slots

| Slot | Konfiguration |
|------|---------------|
| `admin_menu` | `{label: 'Medienbibliothek', icon: 'ti ti-photo', url: 'media_admin.library'}` |

## Settings-Schema

| Key | Type | Default | Beschreibung |
|-----|------|---------|--------------|
| `pexels_api_key` | password | (leer) | Pexels API Key |
| `unsplash_access_key` | password | (leer) | Unsplash Access Key |
| `max_upload_size_mb` | int | 10 | Max. Upload-Größe |
| `auto_resize` | bool | true | Automatisches Resizing |

## Abhängigkeiten

- **v_flask Core**: Auth, DB
- **Pillow**: Bildverarbeitung und Resizing
- **requests**: API-Calls zu Pexels/Unsplash

## Datenbank-Schema

```sql
CREATE TABLE media (
    id INTEGER PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) UNIQUE NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    media_type VARCHAR(20) DEFAULT 'other',
    file_size INTEGER,

    -- Dimensionen
    width INTEGER,
    height INTEGER,

    -- Resize-Varianten
    path_thumbnail VARCHAR(500),  -- 150x150
    path_small VARCHAR(500),      -- 400x400
    path_medium VARCHAR(500),     -- 800x800
    path_large VARCHAR(500),      -- 1200x1200

    -- SEO
    alt_text VARCHAR(200),
    title VARCHAR(200),
    caption TEXT,
    kategorien JSON DEFAULT '[]',

    -- Source Tracking
    source VARCHAR(50) DEFAULT 'upload',
    source_id VARCHAR(100),
    source_url VARCHAR(500),
    photographer VARCHAR(200),

    -- Tracking
    uploaded_by_id INTEGER REFERENCES user(id),
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Storage-Struktur

```
instance/media/
├── 2026/
│   └── 01/
│       ├── abc123_photo.jpg          # Original
│       ├── abc123_photo_thumb.jpg    # 150x150
│       ├── abc123_photo_small.jpg    # 400x400
│       ├── abc123_photo_medium.jpg   # 800x800
│       └── abc123_photo_large.jpg    # 1200x1200
```

## Technische Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| UUID-Prefix im Dateinamen | Verhindert Kollisionen, ermöglicht Original-Filename |
| YYYY/MM Ordnerstruktur | S3-kompatibel, gute Performance bei vielen Dateien |
| Pillow für Resizing | Standard-Library, gut getestet |
| Lazy API-Client Init | Vermeidet Fehler wenn API-Keys nicht gesetzt |
