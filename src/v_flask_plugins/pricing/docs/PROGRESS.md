# Pricing Plugin - Fortschritt & Phasenplan

## Status-Übersicht

| Phase | Status | Fortschritt |
|-------|--------|-------------|
| Phase 1: POC | 🟢 Abgeschlossen | 100% |
| Phase 2: MVP | ⚪ Nicht begonnen | 0% |
| Phase 3: V1 | ⚪ Nicht begonnen | 0% |

**Legende:** ⚪ Nicht begonnen | 🔵 In Arbeit | 🟢 Abgeschlossen

---

## Phase 1: POC (Proof of Concept)

**Ziel:** Kundenspezifische Artikelpreise funktionieren

### Aufgaben

- [x] **1.1 Plugin-Grundstruktur**
  - [x] `__init__.py` mit PricingPlugin Manifest
  - [x] Verzeichnisstruktur angelegt (services/, routes/, templates/)
  - [x] Abhängigkeiten zu PIM und CRM definiert

- [x] **1.2 Datenbank-Models**
  - [x] `pricing_rule` mit Basis-Feldern (customer_id, product_id, price_type, price_value)
  - [ ] Migration erstellen und testen (Host-App erforderlich)

- [x] **1.3 PriceService (Basis)**
  - [x] `get_price()` - Einzelpreis ermitteln
  - [x] Nur rule_type `customer_product` implementiert
  - [x] Keine Staffelpreise, keine Zeitbegrenzung (POC-Scope)

- [x] **1.4 RuleService (Basis)**
  - [x] `create()` - Regel anlegen
  - [x] `update()` - Regel bearbeiten
  - [x] `delete()` - Regel löschen
  - [x] `get_rules_for_customer()` - Regeln auflisten

- [x] **1.5 Admin-UI (Minimal)**
  - [x] Regelliste für Kunde (`rules_list.html`)
  - [x] Regel anlegen/bearbeiten (`rule_form.html`)
  - [x] CSRF-Schutz in allen Formularen

- [x] **1.6 API für Shop**
  - [x] `GET /api/pricing/price/<product>/<customer>`

**Akzeptanzkriterien POC:**
- [x] Admin kann Kundenpreis für einzelnen Artikel anlegen
- [x] Shop kann Kundenpreis abrufen (via API)
- [x] Bei keinem Kundenpreis wird Listenpreis zurückgegeben

**Status:** 🟢 Abgeschlossen

---

## Phase 2: MVP (Minimum Viable Product)

**Ziel:** Vollständige Preislogik mit allen Regeltypen

### Aufgaben

- [ ] **2.1 Alle Regeltypen implementieren**
  - [x] `customer_product` - Kundenspezifischer Artikelpreis
  - [ ] `customer_series` - Kundenspezifischer Serienrabatt
  - [ ] `customer_brand` - Kundenspezifischer Markenrabatt
  - [ ] `customer_manufacturer` - Kundenspezifischer Herstellerrabatt
  - [ ] `customer_product_group` - Kundenspezifischer Warengruppenrabatt
  - [ ] `customer_price_tag` - Kundenspezifischer Preis-Tag-Rabatt
  - [ ] `group_global` - Kundengruppen-Rabatt

- [ ] **2.2 Staffelpreise**
  - [ ] `pricing_tier` Model
  - [ ] Staffelpreis-Logik in PriceService
  - [ ] Admin-UI: Staffeln pro Regel

- [ ] **2.3 Zeitliche Begrenzung**
  - [ ] `valid_from`, `valid_to` in Regeln
  - [ ] Gültigkeitsprüfung in PriceService
  - [ ] Admin-UI: Datum-Felder

- [ ] **2.4 Prioritäts-System**
  - [ ] Prioritäts-Hierarchie implementieren
  - [ ] Manuelle Priorität pro Regel

- [ ] **2.5 Mindestmarge**
  - [ ] MarginService implementieren
  - [ ] Settings für Mindestmarge
  - [ ] Warnung bei Unterschreitung
  - [ ] Flash-Message bei Admin-Eingabe

- [ ] **2.6 Admin-UI Vollständig**
  - [ ] Dashboard mit Statistiken
  - [ ] Regeln nach Kunde suchen
  - [ ] Alle Regeltypen anlegen
  - [ ] Kaskadierende Dropdowns (Hersteller → Marke → Serie)
  - [ ] Margen-Warnung im Formular

- [ ] **2.7 Bulk-API**
  - [ ] `POST /api/pricing/prices` für mehrere Produkte
  - [ ] Performance-Optimierung

**Akzeptanzkriterien MVP:**
- [ ] Alle Regeltypen funktionieren
- [ ] Staffelpreise korrekt berechnet
- [ ] Zeitlich begrenzte Regeln laufen automatisch ab
- [ ] Mindestmarge-Warnung erscheint
- [ ] Shop zeigt Streichpreis + Ersparnis

**Status:** ⚪ Nicht begonnen

---

## Phase 3: V1 (Vollversion)

**Ziel:** Produktionsreife mit Reporting und Import

### Aufgaben

- [ ] **3.1 Preishistorie**
  - [ ] Änderungsprotokoll für Regeln
  - [ ] Wer hat wann was geändert

- [ ] **3.2 CSV-Import**
  - [ ] Preisregeln per CSV importieren
  - [ ] Spalten-Mapping
  - [ ] Validierung und Fehlerprotokoll

- [ ] **3.3 Reporting**
  - [ ] Regeln mit Margen-Warnung
  - [ ] Ablaufende Regeln (nächste 30 Tage)
  - [ ] Umsatz pro Preisregel (aus Shop-Daten)

- [ ] **3.4 Erweiterte Suche**
  - [ ] Regeln nach Produkt suchen
  - [ ] Regeln nach Marke suchen
  - [ ] Regeln nach Gültigkeit filtern

- [ ] **3.5 API-Erweiterungen**
  - [ ] Vollständige CRUD-API für Regeln
  - [ ] Webhook bei Regeländerungen

**Akzeptanzkriterien V1:**
- [ ] Änderungsprotokoll vollständig
- [ ] CSV-Import funktioniert
- [ ] Reporting zeigt kritische Regeln
- [ ] API dokumentiert

**Status:** ⚪ Nicht begonnen

---

## Abhängigkeiten

### Pricing benötigt

| Abhängigkeit | Status | Anmerkung |
|--------------|--------|-----------|
| **PIM Plugin** | 🟢 Vorhanden | Produkte, Marken, Serien, etc. |
| **CRM Plugin** | 🟢 Vorhanden | Kunden, Kundengruppen |
| Toast-Service | ✅ Nicht benötigt | Flask `flash()` reicht für Margen-Warnung |

### Pricing wird benötigt von

| Plugin | Nutzt | Priorität |
|--------|-------|-----------|
| Shop | PriceService für alle Preisanzeigen | Hoch |
| Go POS | PriceService (später) | Niedrig |

---

## Offene Entscheidungen

| # | Frage | Optionen | Entscheidung |
|---|-------|----------|--------------|
| 1 | Toast-Service | Bestehend / Neu | ✅ Flask `flash()` verwenden |
| 2 | Preishistorie | In pricing_rule_history Tabelle / Audit-Log Plugin | Offen (V1) |
| 3 | Webhook-System | Eigenes / Event-Bus | Offen (V1) |

---

## Changelog

### 2026-01-21 - POC Implementierung abgeschlossen

- ✅ Plugin-Struktur erstellt (`__init__.py`, `models.py`)
- ✅ PricingRule Model mit customer_id, product_id, price_type, price_value
- ✅ PriceService mit `get_price()` für Einzelpreis-Berechnung
- ✅ RuleService mit CRUD-Operationen
- ✅ Admin-Routes für Regelverwaltung pro Kunde
- ✅ Templates: rules_list.html, rule_form.html (DaisyUI)
- ✅ API-Route: GET /api/pricing/price/<product_id>/<customer_id>
- ✅ Marketplace-Eintrag in plugins_marketplace.json
- ✅ PROGRESS.md aktualisiert
- 🔜 Nächster Schritt: Migration in Host-App erstellen und testen

### 2025-01-20 - Konzeption abgeschlossen

- ✅ Pricing-Plugin Konzept erarbeitet
- ✅ Preisfindungs-Hierarchie definiert
- ✅ Datenmodell entworfen
- ✅ PriceService Algorithmus dokumentiert
- ✅ SPEC.md erstellt
- ✅ TECH.md erstellt
- ✅ PROGRESS.md erstellt

---

## Hinweise für AI-Code-Agenten

### Vor Implementierung prüfen

1. **Flash-Messages:** V-Flask verwendet Flask's `flash()` mit DaisyUI-Alerts. Kein separater Toast-Service nötig.

2. **Plugin-Abhängigkeiten:** PIM und CRM sind bereits implementiert:
   - `pim_service.products.get_by_id(product_id)` für Produktdaten
   - `crm_service.customers.get_by_id(customer_id)` für Kundendaten

3. **Service-Pattern:** Services als Singleton mit Lazy Loading:
   ```python
   from v_flask_plugins.pricing.services import pricing_service
   result = pricing_service.prices.get_price(product_id, customer_id)
   ```

### Performance-Kritische Stellen

1. **Bulk-Preisabfrage:** Bei Katalogansicht werden viele Preise gleichzeitig abgefragt
   - Nicht N+1 Queries machen
   - Regeln vorladen
   - In-Memory Berechnung

2. **Regelsuche:** Die Preisfindung prüft viele Ebenen
   - Indizes auf häufig gefilterte Spalten
   - Caching erwägen für häufige Kombinationen

### Test-Szenarien

1. **Hierarchie-Test:** Kunde hat Regel auf Marke (10%) und Artikel (Festpreis) → Artikelpreis gewinnt
2. **Staffel-Test:** Menge 1 = 10€, Menge 10 = 9€, Menge 50 = 8€
3. **Ablauf-Test:** Regel gültig bis gestern → wird nicht angewendet
4. **Margen-Test:** Festpreis unter Einkaufspreis → Warnung
