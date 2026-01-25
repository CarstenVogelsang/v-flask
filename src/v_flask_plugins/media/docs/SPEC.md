# Media Plugin - Spezifikation

## Übersicht

Das Media Plugin bietet eine zentrale Medienbibliothek mit Datei-Upload, automatischem Resizing und Stock-Photo-Integration (Pexels, Unsplash). Es stellt wiederverwendbare Komponenten (Media Picker) für andere Plugins bereit.

## Zielgruppe

- **Admins**: Verwaltung der Medienbibliothek
- **Redakteure**: Upload und Auswahl von Bildern
- **Entwickler**: Integration des Media Pickers in eigene Plugins

## User Stories

- Als Admin möchte ich Bilder hochladen und verwalten, damit ich sie in verschiedenen Plugins verwenden kann
- Als Redakteur möchte ich Stock-Fotos suchen und importieren, damit ich professionelle Bilder nutzen kann
- Als Entwickler möchte ich den Media Picker in mein Plugin einbinden, damit Benutzer Bilder auswählen können
- Als Besucher möchte ich optimierte Bilder sehen, die schnell laden

## Funktionale Anforderungen

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | Datei-Upload mit Validierung | Must | POC |
| F2 | Automatisches Resizing (4 Größen) | Must | POC |
| F3 | Admin-UI mit Bibliotheksansicht | Must | MVP |
| F4 | Media Picker Komponente | Must | MVP |
| F5 | Pexels Stock-Photo Integration | Should | MVP |
| F6 | Unsplash Stock-Photo Integration | Should | MVP |
| F7 | SEO-Metadaten (alt_text, title) | Should | V1 |
| F8 | Kategorisierung und Suche | Should | V1 |

## Resize-Presets

| Größe | Dimension | Verwendung |
|-------|-----------|------------|
| `thumbnail` | 150x150px | Vorschau in Listen |
| `small` | 400x400px | Kleine Inline-Bilder |
| `medium` | 800x800px | Standard-Anzeige |
| `large` | 1200x1200px | Hero-Bilder, Vollbild |
| `original` | Unverändert | Download, Archiv |

## Stock-Photo-Attributierung

Bei Pexels und Unsplash ist eine korrekte Attributierung erforderlich:
- Photographername wird gespeichert
- Quell-URL wird gespeichert
- `attribution_html` Property generiert korrekten HTML-Link

## Nicht-funktionale Anforderungen

- **Performance**: Upload < 5s für 10MB Bild
- **Kompatibilität**: JPEG, PNG, GIF, WebP
- **Sicherheit**: Nur authentifizierte Uploads
- **Storage**: S3-kompatible Pfadstruktur (YYYY/MM/uuid_filename.ext)

## Abgrenzung (Out of Scope)

- Video-Upload (ggf. spätere Erweiterung)
- Bildbearbeitung im Browser (Crop, Filter)
- CDN-Integration (sollte auf Infrastruktur-Ebene erfolgen)
