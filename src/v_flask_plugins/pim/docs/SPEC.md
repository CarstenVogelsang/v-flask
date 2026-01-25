# PIM Plugin - Spezifikation

## Übersicht

| Eigenschaft | Wert |
|-------------|------|
| **Plugin-Name** | `pim` |
| **Tabellen-Prefix** | `pim_` |
| **Admin-URLs** | `/admin/pim/` |
| **Abhängigkeiten** | Keine (Core-Plugin) |
| **Konsumenten** | `shop`, `pos`, `wawi` |

## Zweck

Das PIM (Product Information Management) ist ein **Basis-Plugin** für die zentrale Verwaltung von Produktstammdaten. Es stellt Produkte, Kategorien und Bilder für andere Plugins bereit.

---

## User Stories

### MVP - Produktverwaltung

| ID | Als... | möchte ich... | damit... |
|----|--------|---------------|----------|
| PIM-001 | Admin | Produkte anlegen können | ich meinen Katalog aufbauen kann |
| PIM-002 | Admin | Produkte bearbeiten können | ich Daten aktualisieren kann |
| PIM-003 | Admin | Produkte löschen/deaktivieren können | veraltete Produkte nicht mehr erscheinen |
| PIM-004 | Admin | Produkte nach Name/SKU/EAN suchen | ich schnell finde was ich brauche |
| PIM-005 | Admin | Produkte filtern können (Kategorie, Status) | ich Übersicht behalte |
| PIM-006 | Admin | Produktbilder hochladen können | Produkte visuell dargestellt werden |
| PIM-007 | Admin | ein Hauptbild festlegen können | dieses im Katalog angezeigt wird |
| PIM-008 | Admin | Bilder sortieren können | die Reihenfolge in der Galerie stimmt |

### MVP - Kategorien

| ID | Als... | möchte ich... | damit... |
|----|--------|---------------|----------|
| PIM-010 | Admin | Kategorien anlegen können | ich Produkte strukturieren kann |
| PIM-011 | Admin | Kategorien hierarchisch anordnen | ich Unterkategorien haben kann |
| PIM-012 | Admin | Kategorien per Drag & Drop sortieren | die Reihenfolge intuitiv anpassbar ist |
| PIM-013 | Admin | Kategorien deaktivieren können | sie temporär ausgeblendet werden |

### MVP - Steuersätze

| ID | Als... | möchte ich... | damit... |
|----|--------|---------------|----------|
| PIM-020 | Admin | MwSt-Sätze verwalten können | verschiedene Steuersätze verfügbar sind |
| PIM-021 | Admin | einen Standard-Steuersatz festlegen | neue Produkte diesen automatisch erhalten |

### MVP - Import/Export

| ID | Als... | möchte ich... | damit... |
|----|--------|---------------|----------|
| PIM-030 | Admin | Produkte per CSV importieren | ich Massendaten einpflegen kann |
| PIM-031 | Admin | Produkte per CSV exportieren | ich Daten extern bearbeiten kann |

### MVP - Barcodes

| ID | Als... | möchte ich... | damit... |
|----|--------|---------------|----------|
| PIM-040 | Admin | GTIN/EAN-13/UPC eingeben können | alle gängigen Barcodes unterstützt werden |
| PIM-041 | System | Barcodes automatisch erkennen | ich nicht den Typ angeben muss |
| PIM-042 | System | Barcodes validieren | Fehleingaben verhindert werden |

---

## V1 - Geplante Erweiterungen

### Produktvarianten

| ID | Als... | möchte ich... | damit... |
|----|--------|---------------|----------|
| PIM-100 | Admin | Varianten-Attribute definieren (Größe, Farbe) | ich Produktvarianten anlegen kann |
| PIM-101 | Admin | Varianten zu einem Produkt anlegen | z.B. T-Shirt in S/M/L/XL |
| PIM-102 | Admin | je Variante eigene SKU/EAN/Preis/Bestand | Varianten individuell verwaltbar sind |
| PIM-103 | Admin | Varianten-Matrix sehen | ich Übersicht über alle Kombinationen habe |

### Mehrsprachigkeit (Produkttexte)

| ID | Als... | möchte ich... | damit... |
|----|--------|---------------|----------|
| PIM-110 | Admin | Produktname in mehreren Sprachen pflegen | internationale Kunden bedient werden |
| PIM-111 | Admin | Beschreibungen mehrsprachig pflegen | Texte lokalisiert sind |
| PIM-112 | Admin | Sprachen aktivieren/deaktivieren | nur relevante Sprachen angezeigt werden |
| PIM-113 | System | Fallback auf Standardsprache | bei fehlender Übersetzung |

### S3 Bilder-Storage

| ID | Als... | möchte ich... | damit... |
|----|--------|---------------|----------|
| PIM-120 | Admin | Storage-Typ in Einstellungen wählen | ich zwischen lokal und S3 wechseln kann |
| PIM-121 | System | Bilder transparent aus S3 laden | die Anzeige unabhängig vom Storage ist |

---

## Nicht-funktionale Anforderungen

| Bereich | Anforderung |
|---------|-------------|
| **Performance** | Produktliste mit 10.000 Produkten < 1 Sekunde |
| **Suche** | Volltextsuche über Name, SKU, EAN |
| **Bilder** | Automatische Thumbnail-Generierung |
| **Validierung** | Barcode-Prüfsummen validieren |
| **API** | Services für andere Plugins exponieren |

---

## Abgrenzung

### Gehört ins PIM
- Produktstammdaten (Name, Beschreibung, SKU, EAN)
- Kategorien
- Bilder
- Steuersätze
- Einkaufspreise (cost_price)
- Basis-Verkaufspreise (Listenpreis)
- Lagerbestand (Menge, Mindestbestand)
- Varianten (ab V1)
- Mehrsprachige Texte (ab V1)

### Gehört NICHT ins PIM
- Kundenspezifische Preise → Shop-Plugin
- Staffelpreise/Mengenrabatte → Shop-Plugin
- Kundendaten → CRM-Plugin
- Bestellungen → Shop-Plugin
- Kassenvorgänge → POS-Plugin
