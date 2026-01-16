"""E-Commerce & Zahlung Bausteine.

Text modules for payment providers and order processing.
"""

from v_flask_plugins.datenschutz.bausteine import Baustein

PAYPAL = Baustein(
    id='paypal',
    kategorie='zahlung',
    name='PayPal',
    beschreibung='PayPal Zahlungsabwicklung',
    order=10,
    detect_patterns=[r'paypal\.com', r'paypalobjects\.com'],
    text_template='''
### PayPal

Auf dieser Website bieten wir die Bezahlung via PayPal an. Anbieter dieses
Zahlungsdienstes ist die PayPal (Europe) S.à.r.l. et Cie, S.C.A.,
22-24 Boulevard Royal, L-2449 Luxembourg.

Wenn Sie mit PayPal bezahlen, erfolgt eine Übermittlung der von Ihnen
eingegebenen Zahlungsdaten an PayPal.

Die Übermittlung Ihrer Daten an PayPal erfolgt auf Grundlage von
**Art. 6 Abs. 1 lit. b DSGVO** (Verarbeitung zur Erfüllung eines Vertrags).

Die PayPal-Datenschutzerklärung finden Sie unter:
[https://www.paypal.com/de/webapps/mpp/ua/privacy-full](https://www.paypal.com/de/webapps/mpp/ua/privacy-full)
''',
)

STRIPE = Baustein(
    id='stripe',
    kategorie='zahlung',
    name='Stripe',
    beschreibung='Stripe Zahlungsabwicklung',
    order=20,
    detect_patterns=[r'stripe\.com', r'js\.stripe\.com'],
    text_template='''
### Stripe

Für Zahlungsvorgänge auf dieser Website nutzen wir den Zahlungsdienstleister
Stripe. Anbieter ist die Stripe Payments Europe, Ltd., 1 Grand Canal Street Lower,
Grand Canal Dock, Dublin, Irland.

Wenn Sie eine Zahlung über Stripe durchführen, werden die von Ihnen eingegebenen
Zahlungsdaten (z.B. Kreditkartennummer, Ablaufdatum, CVV) an Stripe übermittelt.

Die Übermittlung dieser Daten erfolgt auf Grundlage von **Art. 6 Abs. 1 lit. b DSGVO**
(Vertragserfüllung) und im Rahmen unseres berechtigten Interesses an einer
effizienten und sicheren Zahlungsabwicklung (**Art. 6 Abs. 1 lit. f DSGVO**).

Die Datenschutzerklärung von Stripe finden Sie unter:
[https://stripe.com/de/privacy](https://stripe.com/de/privacy)
''',
)

KLARNA = Baustein(
    id='klarna',
    kategorie='zahlung',
    name='Klarna',
    beschreibung='Klarna Zahlungsabwicklung (Kauf auf Rechnung, Ratenkauf)',
    order=30,
    detect_patterns=[r'klarna\.com', r'klarnacdn\.net'],
    text_template='''
### Klarna

Auf dieser Website bieten wir die Bezahlung via Klarna an. Anbieter ist die
Klarna Bank AB, Sveavägen 46, 111 34 Stockholm, Schweden.

Klarna bietet verschiedene Zahlungsoptionen an (z.B. Kauf auf Rechnung, Ratenkauf).
Wenn Sie sich für eine Klarna-Zahlungsoption entscheiden, erhebt Klarna
verschiedene personen- und bestellbezogene Daten.

Die Übermittlung Ihrer Daten an Klarna erfolgt auf Grundlage von
**Art. 6 Abs. 1 lit. b DSGVO** (Vertragserfüllung) und im Rahmen unseres
berechtigten Interesses an der Bereitstellung attraktiver Zahlungsoptionen
(**Art. 6 Abs. 1 lit. f DSGVO**).

Die Datenschutzerklärung von Klarna finden Sie unter:
[https://www.klarna.com/de/datenschutz/](https://www.klarna.com/de/datenschutz/)
''',
)

BESTELLUNG = Baustein(
    id='bestellung',
    kategorie='zahlung',
    name='Bestellabwicklung',
    beschreibung='Allgemeine Datenverarbeitung bei Bestellungen',
    order=100,
    text_template='''
### Verarbeiten von Daten (Bestell- und Vertragsdaten)

Wir erheben, verarbeiten und nutzen personenbezogene Daten nur, soweit sie für
die Begründung, inhaltliche Ausgestaltung oder Änderung des Rechtsverhältnisses
erforderlich sind (Bestandsdaten). Personenbezogene Daten über die Inanspruchnahme
unserer Website (Nutzungsdaten) erheben, verarbeiten und nutzen wir nur, soweit
dies erforderlich ist, um dem Nutzer die Inanspruchnahme des Dienstes zu
ermöglichen oder abzurechnen.

Die erhobenen Kundendaten werden nach Abschluss des Auftrags oder Beendigung der
Geschäftsbeziehung gelöscht. Gesetzliche Aufbewahrungsfristen bleiben unberührt.

Die Rechtsgrundlage für die Datenverarbeitung ist **Art. 6 Abs. 1 lit. b DSGVO**
(Erfüllung eines Vertrags oder Durchführung vorvertraglicher Maßnahmen).
''',
)

ZAHLUNG_BAUSTEINE = [
    PAYPAL,
    STRIPE,
    KLARNA,
    BESTELLUNG,
]
