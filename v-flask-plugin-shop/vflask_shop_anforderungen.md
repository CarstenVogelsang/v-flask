# Vflask Shop POC - Anforderungsdokument

## Projektübersicht

**Projektname:** Vflask Shop POC  
**Typ:** Proof of Concept für ein einfaches Shop-System  
**Framework:** Vflask (Python/Flask-basiert)  
**Zielmarkt:** Deutschland (rechtskonforme Umsetzung)  
**Beispiel-Branche:** Schreibwaren-Shop (angelehnt an legami.com)

---

## 1. Technische Rahmenbedingungen

### Stack
- **Backend:** Python mit Vflask Framework
- **Frontend:** Jinja2 Templates, modernes CSS (Tailwind CSS oder eigenes CSS)
- **Datenbank:** SQLite für POC (später migrierbar auf PostgreSQL)
- **Payment:** PayPal Checkout (JavaScript SDK + REST API)
- **Session:** Flask-Session für Warenkorb

### Projektstruktur
```
vflask_shop/
├── app.py                    # Hauptanwendung
├── config.py                 # Konfiguration
├── models/
│   ├── __init__.py
│   ├── product.py           # Produkt, Kategorie
│   └── order.py             # Bestellung, Bestellposition
├── routes/
│   ├── __init__.py
│   ├── shop.py              # Shop-Routen (Kategorien, Produkte)
│   ├── cart.py              # Warenkorb-Routen
│   ├── checkout.py          # Checkout & Payment
│   └── legal.py             # Rechtliche Seiten
├── services/
│   ├── paypal.py            # PayPal Integration
│   └── email.py             # E-Mail-Versand
├── templates/
│   ├── base.html            # Basis-Template mit Header/Footer
│   ├── components/
│   │   ├── consent_banner.html
│   │   ├── product_card.html
│   │   └── cart_icon.html
│   ├── shop/
│   │   ├── index.html       # Startseite
│   │   ├── category.html    # Kategorieübersicht
│   │   └── product.html     # Produktdetailseite
│   ├── cart/
│   │   └── cart.html        # Warenkorb
│   ├── checkout/
│   │   ├── checkout.html    # Checkout-Formular
│   │   ├── payment.html     # Zahlungsseite
│   │   └── success.html     # Bestellbestätigung
│   └── legal/
│       ├── impressum.html
│       ├── datenschutz.html
│       ├── agb.html
│       └── widerruf.html
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── shop.js          # Warenkorb-Interaktionen
│   │   ├── consent.js       # Cookie-Consent
│   │   └── paypal.js        # PayPal Integration
│   └── images/
│       └── products/        # Produktbilder
└── data/
    └── products.json        # Produktdaten für POC (statt DB-Admin)
```

---

## 2. Funktionale Anforderungen

### 2.1 Startseite
- Header mit Logo, Suche (optional für POC), Warenkorb-Icon mit Anzahl
- Hauptnavigation mit Kategorien
- Hero-Bereich oder Featured Products
- Footer mit rechtlichen Links

### 2.2 Kategorien
**Kategorie-Struktur (Beispieldaten):**
```
Stifte und mehr
├── Schreibwaren
├── Hefte
├── Notizbücher
├── Schreibtischzubehör
├── Schule
└── Lesezeichen

Gelstifte (Unterkategorie von Stifte)
├── Löschbare Gelstifte
├── Minen für Löschstifte
├── Gelstifte Lovely Friends
├── Kugelschreiber und Gelstifte
├── Squishy-Gelstifte
├── Leuchtende Kugelschreiber
├── Bunte Gelstifte
├── Textmarker und Filzstifte
└── Bleistifte und Buntstifte
```

**Kategorieseite:**
- Kategoriename als Überschrift
- Breadcrumb-Navigation
- Produktliste als Grid (responsive: 2-4 Spalten)
- Jedes Produkt zeigt: Bild, Name, Preis, "In den Warenkorb"-Button
- Optional: Filter/Sortierung (für POC nicht zwingend)

### 2.3 Produktdetailseite
**Elemente:**
- Breadcrumb-Navigation
- Produktbild (groß, evtl. Galerie für mehrere Bilder)
- Produktname
- Preis (Bruttopreis mit MwSt.-Hinweis)
- Kurzbeschreibung
- Ausführliche Beschreibung (ausklappbar "Mehr anzeigen")
- Varianten-Auswahl (falls vorhanden, z.B. Farbe/Motiv)
- Verfügbarkeitsstatus
- Mengenauswahl (+/- Buttons)
- "IN DEN WARENKORB"-Button (prominent)
- Versandhinweis (z.B. "Versand über DHL")

### 2.4 Warenkorb
**Funktionen:**
- Übersicht aller Produkte im Warenkorb
- Mengenänderung möglich
- Einzelpreis und Gesamtpreis pro Position
- Zwischensumme
- Versandkosten (Pauschal oder nach Gewicht/Wert)
- Gesamtsumme (inkl. MwSt.)
- "Weiter einkaufen"-Button
- "Zur Kasse"-Button

**Session-basiert:**
- Warenkorb in Flask-Session speichern
- Warenkorb bleibt erhalten bis Session endet

### 2.5 Checkout-Prozess

**Schritt 1: Kundendaten**
- Anrede, Vorname, Nachname
- E-Mail-Adresse
- Telefon (optional)
- Lieferadresse (Straße, Hausnummer, PLZ, Ort, Land = Deutschland)
- Abweichende Rechnungsadresse (optional)

**Schritt 2: Versandart**
- DHL Standardversand (Preis anzeigen)
- Lieferzeit-Angabe (z.B. "3-5 Werktage")

**Schritt 3: Zahlungsart**
- PayPal Checkout (einzige Option für POC)

**Schritt 4: Bestellübersicht**
- Zusammenfassung aller Produkte
- Lieferadresse
- Versandart und -kosten
- Zahlungsart
- Gesamtbetrag

**Rechtliche Checkboxen (PFLICHT vor Bestellung):**
- [ ] Ich habe die AGB gelesen und akzeptiere diese.
- [ ] Ich habe die Widerrufsbelehrung zur Kenntnis genommen.
- [ ] Ich habe die Datenschutzerklärung zur Kenntnis genommen.

**Bestell-Button:**
- Text: **"Zahlungspflichtig bestellen"** (Button-Lösung nach deutschem Recht!)
- NICHT: "Bestellen", "Kaufen", "Weiter"

### 2.6 PayPal Integration
**Ablauf:**
1. Nach Klick auf "Zahlungspflichtig bestellen" → PayPal Checkout öffnet sich
2. Kunde authentifiziert sich bei PayPal
3. Zahlung wird autorisiert
4. Weiterleitung zurück zum Shop
5. Bestellung wird in Datenbank gespeichert
6. Bestellbestätigung wird angezeigt
7. Bestätigungs-E-Mail wird versendet

**Technische Umsetzung:**
- PayPal JavaScript SDK für Frontend
- PayPal REST API v2 für Backend (Create Order, Capture Payment)
- Sandbox-Modus für Entwicklung

### 2.7 Bestellbestätigung
- "Vielen Dank für Ihre Bestellung!"
- Bestellnummer
- Zusammenfassung der Bestellung
- Hinweis auf Bestätigungs-E-Mail
- Link zur Startseite

---

## 3. Rechtliche Anforderungen Deutschland

### 3.1 Cookie-Consent-Banner
**Anforderungen:**
- Erscheint beim ersten Besuch
- Unterscheidung: Notwendige / Marketing / Statistik Cookies
- "Alle akzeptieren" und "Nur notwendige" Buttons
- Link zu Datenschutzerklärung
- Einstellung speichern (LocalStorage)
- Muss vor dem Laden von Tracking-Scripts erscheinen

**Für POC reicht:**
- Einfacher Banner mit Hinweis auf Cookies
- Akzeptieren-Button
- Link zur Datenschutzerklärung

### 3.2 Preisangabenverordnung (PAngV)
**Pflichtangaben bei Preisen:**
- Bruttopreise (inkl. MwSt.)
- Hinweis: "inkl. MwSt." oder "inkl. 19% MwSt."
- Versandkostenhinweis: "zzgl. Versandkosten" mit Link zur Versandkostenseite
- Bei Grundpreispflichtigen Waren: Grundpreis pro Mengeneinheit

**Beispiel-Darstellung:**
```
1,95 €
inkl. MwSt., zzgl. Versandkosten
```

### 3.3 Impressum
**Pflichtangaben nach § 5 TMG:**
- Vollständiger Name/Firma
- Anschrift (Straße, PLZ, Ort)
- Kontaktdaten (E-Mail, Telefon)
- Vertretungsberechtigte Person(en)
- Handelsregister, Registergericht, Registernummer (falls vorhanden)
- Umsatzsteuer-ID (falls vorhanden)
- Verantwortlicher für Inhalte (§ 55 RStV)

### 3.4 Datenschutzerklärung
**Inhalte:**
- Verantwortlicher und Kontaktdaten
- Erhobene Daten und Zweck
- Rechtsgrundlagen (DSGVO)
- Speicherdauer
- Weitergabe an Dritte (PayPal, DHL)
- Betroffenenrechte
- Cookies und Tracking
- Hinweis auf Beschwerderecht

### 3.5 AGB (Allgemeine Geschäftsbedingungen)
**Inhalte:**
- Geltungsbereich
- Vertragsschluss
- Preise und Zahlung
- Lieferung und Versand
- Eigentumsvorbehalt
- Gewährleistung/Mängelhaftung
- Haftungsbeschränkung
- Schlussbestimmungen

### 3.6 Widerrufsbelehrung
**Für Verbraucher (B2C):**
- 14 Tage Widerrufsrecht
- Muster-Widerrufsformular (Pflicht!)
- Ausnahmen vom Widerrufsrecht
- Folgen des Widerrufs (Rückzahlung)

### 3.7 Versandkosten-Seite
- Übersicht der Versandkosten
- Liefergebiete (nur Deutschland für POC)
- Lieferzeiten

---

## 4. Datenmodell

### Product
```python
class Product:
    id: str                    # Eindeutige ID
    name: str                  # Produktname
    slug: str                  # URL-freundlicher Name
    description_short: str     # Kurzbeschreibung
    description_long: str      # Ausführliche Beschreibung
    price: Decimal             # Bruttopreis in EUR
    tax_rate: Decimal          # MwSt.-Satz (0.19 oder 0.07)
    images: List[str]          # Bildpfade
    category_id: str           # Kategorie-Zuordnung
    variants: List[Variant]    # Varianten (optional)
    in_stock: bool             # Verfügbarkeit
    weight: int                # Gewicht in Gramm (für Versand)
```

### Category
```python
class Category:
    id: str
    name: str
    slug: str
    parent_id: str | None      # Für Unterkategorien
    description: str
    image: str | None
```

### CartItem (Session)
```python
class CartItem:
    product_id: str
    variant_id: str | None
    quantity: int
    price: Decimal             # Preis zum Zeitpunkt des Hinzufügens
```

### Order
```python
class Order:
    id: str
    order_number: str          # Bestellnummer (z.B. ORD-2024-00001)
    created_at: datetime
    status: str                # pending, paid, shipped, completed, cancelled
    
    # Kunde
    customer_email: str
    customer_phone: str | None
    
    # Adressen
    billing_address: Address
    shipping_address: Address
    
    # Positionen
    items: List[OrderItem]
    
    # Beträge
    subtotal: Decimal
    shipping_cost: Decimal
    tax_amount: Decimal
    total: Decimal
    
    # Zahlung
    payment_method: str        # paypal
    payment_id: str            # PayPal Transaction ID
    paid_at: datetime | None
```

---

## 5. API-Endpunkte

### Shop
- `GET /` - Startseite
- `GET /kategorie/<slug>` - Kategorieseite
- `GET /produkt/<slug>` - Produktdetailseite
- `GET /suche?q=<query>` - Suchergebnisse (optional)

### Warenkorb
- `GET /warenkorb` - Warenkorb anzeigen
- `POST /warenkorb/hinzufuegen` - Produkt hinzufügen
- `POST /warenkorb/aktualisieren` - Menge ändern
- `POST /warenkorb/entfernen` - Produkt entfernen

### Checkout
- `GET /kasse` - Checkout-Formular
- `POST /kasse/kundendaten` - Kundendaten speichern
- `GET /kasse/uebersicht` - Bestellübersicht
- `POST /kasse/bestellen` - Bestellung aufgeben

### PayPal
- `POST /api/paypal/create-order` - PayPal Order erstellen
- `POST /api/paypal/capture-order` - Zahlung abschließen

### Rechtliches
- `GET /impressum`
- `GET /datenschutz`
- `GET /agb`
- `GET /widerruf`
- `GET /versandkosten`

---

## 6. Design-Richtlinien

### Allgemein
- Modern, clean, professionell
- Viel Weißraum
- Klare Typografie
- Responsive Design (Mobile First)
- Farben: Dezent, ein Akzentfarbe für CTAs (z.B. Rot/Coral wie bei Legami)

### Komponenten
- **Buttons:** Abgerundete Ecken, klare Hover-States
- **Produktkarten:** Weißer Hintergrund, leichter Schatten, Bild oben
- **Navigation:** Sticky Header, Mega-Menü für Kategorien
- **Footer:** Dunkel, mit allen wichtigen Links

### Typografie
- Headline: Sans-serif, bold
- Body: Sans-serif, regular
- Schriftgrößen responsiv

---

## 7. Beispieldaten

### Kategorien
```json
[
  {"id": "stifte", "name": "Stifte und mehr", "slug": "stifte-und-mehr", "parent_id": null},
  {"id": "schreibwaren", "name": "Schreibwaren", "slug": "schreibwaren", "parent_id": "stifte"},
  {"id": "hefte", "name": "Hefte", "slug": "hefte", "parent_id": "stifte"},
  {"id": "notizbuecher", "name": "Notizbücher", "slug": "notizbuecher", "parent_id": "stifte"},
  {"id": "gelstifte", "name": "Löschbare Gelstifte", "slug": "loeschbare-gelstifte", "parent_id": "stifte"}
]
```

### Produkte
```json
[
  {
    "id": "gelstift-corgi",
    "name": "Löschbarer Gelstift Corgi „Feelin' Corgeous"",
    "slug": "loeschbarer-gelstift-corgi-feelin-corgeous",
    "description_short": "Der löschbare Gelstift Corgi mit thermosensitiver schwarzer Tinte von Legami lässt jeden Tippfehler verschwinden – sooo british!",
    "description_long": "Bye bye, Englischfehler! Der löschbare Gelstift Corgi mit thermosensitiver schwarzer Tinte von Legami lässt jeden Tippfehler verschwinden – sooo british! Die Tinte verschwindet durch die Reibungswärme beim Radieren mit dem integrierten Radiergummi am Stiftende.",
    "price": 1.95,
    "tax_rate": 0.19,
    "images": ["gelstift-corgi-1.jpg", "gelstift-corgi-2.jpg"],
    "category_id": "gelstifte",
    "variants": [
      {"id": "corgi", "name": "Corgi", "image": "variant-corgi.jpg"},
      {"id": "cat", "name": "Katze", "image": "variant-cat.jpg"},
      {"id": "pig", "name": "Schwein", "image": "variant-pig.jpg"}
    ],
    "in_stock": true,
    "weight": 15
  }
]
```

---

## 8. Versandkosten

### Für POC: Einfache Pauschale
- Deutschland: 4,95 € (DHL Paket)
- Versandkostenfrei ab 50 € Bestellwert

---

## 9. E-Mail-Templates

### Bestellbestätigung
- Betreff: "Ihre Bestellung bei [Shopname] - Bestellnummer: ORD-XXXX"
- Inhalt:
  - Anrede
  - Bestellübersicht (Produkte, Preise)
  - Lieferadresse
  - Zahlungsinformation
  - Voraussichtliche Lieferzeit
  - Kontaktdaten für Rückfragen
  - Widerrufsbelehrung (Kurzform mit Link)

---

## 10. Nicht im Scope (für POC)

- [ ] Backend-Verwaltung / Admin-Panel
- [ ] Benutzerregistrierung / Login
- [ ] Bestellhistorie für Kunden
- [ ] Bewertungen / Reviews
- [ ] Gutscheine / Rabattcodes
- [ ] Newsletter-Anmeldung
- [ ] DHL-API-Integration (Tracking, Labels)
- [ ] Mehrere Zahlungsarten
- [ ] Mehrsprachigkeit
- [ ] Mehrere Länder

---

## 11. Nächste Schritte nach POC

1. **Admin-Panel** für Produktverwaltung
2. **Stripe** als alternative Zahlungsart
3. **Benutzerkonten** mit Bestellhistorie
4. **Plugin-Struktur** für Vflask Core Integration
5. **Gastro-Erweiterung** (Speisekarte, Tischreservierung, Abholung)

---

## 12. Testszenarien

### Happy Path
1. Startseite aufrufen → Consent-Banner akzeptieren
2. Kategorie "Stifte und mehr" öffnen
3. Unterkategorie "Löschbare Gelstifte" öffnen
4. Produkt "Gelstift Corgi" anklicken
5. Variante wählen, Menge 2, "In den Warenkorb"
6. Warenkorb öffnen, prüfen
7. "Zur Kasse" klicken
8. Kundendaten eingeben
9. Versandart bestätigen
10. Checkboxen aktivieren (AGB, Widerruf, Datenschutz)
11. "Zahlungspflichtig bestellen" klicken
12. PayPal-Zahlung durchführen (Sandbox)
13. Bestellbestätigung sehen
14. E-Mail erhalten

### Edge Cases
- Leerer Warenkorb → Zur Kasse
- Ungültige PLZ eingeben
- Checkboxen nicht aktiviert → Bestellen
- PayPal-Zahlung abbrechen
- Produkt nicht mehr verfügbar

---

*Dokument erstellt für: Vflask Shop POC*  
*Stand: Januar 2025*
