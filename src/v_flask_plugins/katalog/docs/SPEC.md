# Katalog Plugin - Spezifikation

## Übersicht

Das Katalog Plugin stellt PDF-Kataloge als Blätterkataloge im Browser dar (PDF.js) und bietet Download-Funktionalität mit Tracking. Ideal für Hersteller-Portale mit Produktkatalogen.

## Zielgruppe

- **Admins**: Upload und Verwaltung von PDF-Katalogen
- **Besucher**: Ansicht und Download von Katalogen

## User Stories

- Als Admin möchte ich PDF-Kataloge hochladen und kategorisieren, damit Besucher sie finden
- Als Besucher möchte ich Kataloge im Browser durchblättern, ohne sie herunterladen zu müssen
- Als Admin möchte ich sehen wie oft Kataloge angesehen/heruntergeladen wurden

## Funktionale Anforderungen

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | PDF-Upload mit Kategorisierung | Must | POC |
| F2 | PDF-Viewer im Browser (PDF.js) | Must | POC |
| F3 | Download mit Counter | Must | MVP |
| F4 | View-Counter | Should | MVP |
| F5 | Cover-Bild Vorschau | Should | MVP |
| F6 | Login-Pflicht für Downloads | Could | V1 |

## Kategorien

Das Plugin verwendet vordefinierte Kategorien:
- Hauptkatalog
- Neuheiten
- Aktionen/Angebote
- Preislisten
- Technische Dokumente

## Nicht-funktionale Anforderungen

- **Performance**: PDF-Streaming, keine vollständigen Downloads
- **Sicherheit**: Validierung des Dateityps
- **UX**: Responsive PDF-Viewer

## Abgrenzung (Out of Scope)

- PDF-Bearbeitung im Browser
- Volltextsuche in PDFs
- Wasserzeichen
