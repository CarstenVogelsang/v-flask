# Shop Plugin - Spezifikation

## Übersicht

Modulares Shop-System für v-flask mit initialem Fokus auf B2B-Funktionalität. Ermöglicht Geschäftskunden schnelle Bestellungen mit kundenspezifischen Preisen und kuratierten Produktbereichen.

## Zielgruppe

- **Betreiber:** Unternehmen, die an andere Unternehmen verkaufen (B2B)
- **Kunden:** Geschäftskunden mit Login, die regelmäßig bestellen
- **Admins:** Shop-Betreiber, die Bestellungen verwalten und Preise pflegen

## User Stories

### Kunde (B2B)

- Als Geschäftskunde möchte ich mich einloggen, damit ich meine personalisierten Preise sehe
- Als Geschäftskunde möchte ich auf der Startseite "Meine Produkte" sehen, damit ich schnell Nachbestellungen mache
- Als Geschäftskunde möchte ich Produkte zu "Meine Produkte" hinzufügen, damit ich sie später schneller finde
- Als Geschäftskunde möchte ich per SKU + Menge bestellen, damit ich große Bestellungen effizient aufgebe
- Als Geschäftskunde möchte ich meine Bestellhistorie sehen, damit ich vergangene Bestellungen nachvollziehen kann
- Als Geschäftskunde möchte ich den Bestellstatus verfolgen, damit ich weiß, wann meine Ware kommt

### Admin/Betreiber

- Als Admin möchte ich kundenspezifische Preise pflegen, damit ich individuelle Konditionen anbieten kann
- Als Admin möchte ich Produkte für Kunden kuratieren, damit deren "Meine Produkte"-Bereich vorbefüllt ist
- Als Admin möchte ich Bestellungen mit Status-Workflow verwalten, damit ich den Überblick behalte
- Als Admin möchte ich die Selbstregistrierung aktivieren/deaktivieren, damit ich kontrolliere, wer Kunde wird
- Als Admin möchte ich ein Dashboard mit KPIs sehen, damit ich den Shop-Erfolg messe

## Funktionale Anforderungen

### Frontend (Shop)

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | Kunde kann sich einloggen/ausloggen | Must | POC |
| F2 | Kunde sieht Kategoriebaum (aus PIM) | Must | POC |
| F3 | Kunde sieht Produktliste mit Pagination | Must | POC |
| F4 | Kunde sieht Produktdetail mit seinem Preis | Must | POC |
| F5 | Kunde sieht "Meine Produkte" auf Startseite | Must | MVP |
| F6 | Kunde kann Produkte zu "Meine Produkte" hinzufügen | Must | MVP |
| F7 | Kunde kann Warenkorb befüllen | Must | MVP |
| F8 | Kunde kann Mengen im Warenkorb ändern | Must | MVP |
| F9 | Kunde kann Bestellung aufgeben | Must | MVP |
| F10 | Kunde sieht Bestellhistorie | Must | MVP |
| F11 | Kunde kann Produkte suchen | Should | MVP |
| F12 | Kunde kann Schnellbestellung (SKU+Menge) | Should | V1 |
| F13 | Kunde kann Passwort zurücksetzen | Should | V1 |
| F14 | Selbstregistrierung via Fragebogen | Could | V1 |

### Backend (Admin)

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| A1 | Admin sieht Bestellübersicht | Must | POC |
| A2 | Admin sieht Bestelldetails | Must | POC |
| A3 | Admin kann Bestellstatus ändern | Must | MVP |
| A4 | Admin kann kundenspez. Preise pflegen | Must | MVP |
| A5 | Admin kann Produkte für Kunden kuratieren | Must | MVP |
| A6 | Admin sieht Dashboard mit KPIs | Should | MVP |
| A7 | Admin kann Shop-Einstellungen verwalten | Should | MVP |
| A8 | Admin kann Bulk-Kuratierung | Could | V1 |

## Nicht-funktionale Anforderungen

- **Performance:** Produktliste < 200ms, Checkout < 500ms
- **Sicherheit:** CSRF-Schutz, Session-basierte Auth, nur eingeloggte Kunden
- **Abhängigkeiten:** Benötigt `pim` und `crm` Plugins, optional `fragebogen`
- **Datenbank:** Tabellen-Prefix `shop_`
- **URLs:** Frontend unter `/shop/`, Admin unter `/admin/shop/`

## Abgrenzung (Out of Scope für MVP)

- Zahlungsabwicklung (Payment Gateway Integration)
- Versandkostenberechnung
- Gutschein-/Rabattsystem
- Mehrsprachigkeit
- Multi-Mandanten (ein Shop pro Installation)
- B2C-Modus (geplant für spätere Version)
- Gast-Checkout
- Layout-/Theme-Anpassung durch Betreiber

## Abhängigkeiten

```
shop
├── requires: pim (Produkte, Kategorien, Bilder)
├── requires: crm (Kunden, Adressen)
└── optional: fragebogen (Selbstregistrierung)
```

## Glossar

| Begriff | Bedeutung |
|---------|-----------|
| Kuratierte Produkte | Vom Admin für einen Kunden vorausgewählte Produkte |
| Meine Produkte | Persönlicher Bereich mit kuratierten + selbst hinzugefügten Produkten |
| Schnellbestellung | Direkteingabe von SKU + Menge ohne Katalog-Navigation |
| Kundenspez. Preis | Individueller Preis für einen Kunden, überschreibt Listenpreis |
