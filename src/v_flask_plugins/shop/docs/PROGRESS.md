# Shop Plugin - Fortschritt

## Aktuelle Phase: POC

## Phasen-Übersicht

### Phase 1: POC (Proof of Concept)
**Ziel:** Grundstruktur und minimaler Durchstich Katalog → Warenkorb → Bestellung

- [x] Plugin-Struktur erstellt (`__init__.py`, Manifest)
- [x] Models definiert (Cart, CartItem, Order, OrderItem, OrderStatusHistory)
- [x] Services erstellt (CartService, OrderService, CatalogService)
- [x] Public Blueprint mit Basis-Routes
- [x] Admin Blueprint mit Basis-Routes
- [x] Login/Logout für Kunden (Integration mit CRM CustomerAuth)
- [x] Kategorie-Ansicht (Produkte aus PIM)
- [x] Produkt-Detail (mit kundenspezifischem Preis via Pricing)
- [x] Warenkorb: Hinzufügen, Anzeigen, Mengen ändern, Entfernen
- [x] Checkout: Bestellung erstellen mit Bestellbestätigung
- [x] Admin: Bestellliste mit Status-Filter
- [x] Admin: Bestelldetail mit Status-Änderung
- [ ] Migration erstellen und testen (Host-App erforderlich)

**Status:** 🟢 Abgeschlossen (Code fertig, Migration ausstehend)

**Erfolgskriterium:** Ein Kunde kann sich einloggen, ein Produkt in den Warenkorb legen und eine Bestellung aufgeben. Admin sieht die Bestellung.

---

### Phase 2: MVP (Minimum Viable Product)
**Ziel:** Vollständig nutzbar für erste echte Kunden

**Frontend:**
- [ ] "Meine Produkte" auf Startseite
- [ ] Produkte zu Favoriten hinzufügen/entfernen
- [ ] Vollständiger Checkout mit Adressauswahl
- [ ] Bestellhistorie für Kunden
- [ ] Bestelldetail-Ansicht für Kunden
- [ ] Produktsuche
- [ ] Pagination in Listen

**Backend:**
- [ ] Dashboard mit KPIs (Neue Bestellungen, Umsatz)
- [ ] Kundenspezifische Preise pflegen (Link zu Pricing)
- [ ] Produkte für Kunden kuratieren
- [ ] Shop-Einstellungen

**Status:** ⚪ Nicht begonnen

**Erfolgskriterium:** Shop ist produktiv nutzbar. Admin kann Preise und Kuratierung pflegen. Kunden können ihren persönlichen Bereich nutzen.

---

### Phase 3: V1 (Erste Release-Version)
**Ziel:** Production-ready mit allen geplanten Features

**Features:**
- [ ] Schnellbestellung (SKU + Menge)
- [ ] Passwort vergessen/zurücksetzen
- [ ] Selbstregistrierung via Fragebogen (optional)
- [ ] Bulk-Kuratierung (mehrere Produkte auf einmal)
- [ ] E-Mail-Benachrichtigungen (Bestellbestätigung, Status-Update)

**Technisch:**
- [ ] Error Handling vollständig
- [ ] Input-Validierung
- [ ] Tests (Unit + Integration)
- [ ] Performance-Optimierung (DB-Queries)
- [ ] Dokumentation vollständig
- [ ] Code Review

**Status:** ⚪ Nicht begonnen

**Erfolgskriterium:** Plugin ist stabil, getestet und dokumentiert. Kann als Standard-Lösung ausgerollt werden.

---

### Phase 4: Erweiterungen (Post-V1)
**Ziel:** Zusätzliche Features nach Bedarf

- [ ] B2C-Modus (Endkunden, Gast-Checkout)
- [ ] Zahlungsintegration
- [ ] Versandkostenberechnung
- [ ] Gutschein-System
- [ ] Export (CSV, PDF-Rechnung)
- [ ] API für externe Anbindung
- [ ] Theme-/Layout-Anpassung

**Status:** ⚪ Geplant

---

## Abhängigkeiten-Status

| Plugin | Status | Benötigt für |
|--------|--------|--------------|
| `pim` | 🟢 Vorhanden | Phase 1 - Produkte, Kategorien |
| `crm` | 🟢 Vorhanden | Phase 1 - Kunden, Adressen, Auth |
| `pricing` | 🟢 Vorhanden | Phase 1 - Kundenspezifische Preise |
| `fragebogen` | ⚪ Vorhanden | Phase 3 - Selbstregistrierung (optional) |

**Alle Abhängigkeiten für POC sind erfüllt!**

---

## Changelog

### 2026-01-21 - POC Implementierung abgeschlossen

- ✅ Plugin-Struktur erstellt (`__init__.py` mit ShopPlugin Manifest)
- ✅ Models: Cart, CartItem, Order, OrderItem, OrderStatusHistory
- ✅ Services: CartService, OrderService, CatalogService mit shop_service Facade
- ✅ Auth-Routes: Login/Logout via CRM CustomerAuth
- ✅ Public-Routes: Home, Category, Product, Cart, Checkout
- ✅ Admin-Routes: Orders List, Order Detail, Status Change
- ✅ Templates: 7 Public (base, login, home, category, product, cart, checkout)
- ✅ Templates: 2 Admin (orders_list, order_detail)
- ✅ Marketplace-Eintrag in plugins_marketplace.json
- ✅ Session-basierte Kunden-Auth (getrennt von Admin flask_login)
- ✅ Warenkorb in DB (persistent über Sessions)
- ✅ Produkt-/Preis-Snapshots in Bestellungen
- 🔜 Nächster Schritt: Migration in Host-App erstellen und testen

### 2025-01-20 - Konzeption abgeschlossen

- ✅ Plugin-Konzept erarbeitet
- ✅ Entscheidung: Plugin heißt `shop` (nicht `b2b-shop`)
- ✅ Abhängigkeiten definiert: `pim`, `crm`, `pricing`
- ✅ SPEC.md erstellt mit User Stories und Anforderungen
- ✅ TECH.md erstellt mit Architektur und Datenmodell
- ✅ PROGRESS.md erstellt mit Phasenplan

---

## Beantwortete Fragen

1. **PIM-Struktur:** ✅ PIM hat Product, Category, ProductImage Models + pim_service
2. **CRM-Auth:** ✅ CRM hat CustomerAuth mit crm_service.auth.authenticate()
3. **Pricing:** ✅ Pricing-Plugin liefert kundenspezifische Preise via pricing_service.prices.get_price()
4. **Bestellnummer:** ✅ Format `ORD-YYYY-NNNNN` (z.B. ORD-2026-00001)
5. **MwSt:** ✅ Global 19%, Preise sind Netto (MwSt wird beim Checkout addiert)
