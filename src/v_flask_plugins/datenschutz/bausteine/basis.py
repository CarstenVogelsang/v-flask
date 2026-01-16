"""Basis-Bausteine for every website.

These are fundamental text modules that apply to virtually every website:
- Server logs (IP addresses)
- SSL/TLS encryption
- Hosting provider information
- Technical cookies

Text sources: LDI NRW Muster, IHK München
"""

from v_flask_plugins.datenschutz.bausteine import Baustein

# Server-Logfiles (always applicable)
SERVER_LOGS = Baustein(
    id='server_logs',
    kategorie='basis',
    name='Server-Logfiles',
    beschreibung='Automatische Erfassung von Zugriffsdaten (IP-Adressen)',
    optional=False,  # Always required - every website has server logs
    order=10,
    text_template='''
### Server-Logfiles

Der Provider dieser Website erhebt und speichert automatisch Informationen in
sogenannten Server-Logfiles, die Ihr Browser automatisch übermittelt. Dies sind:

- Browsertyp und Browserversion
- Verwendetes Betriebssystem
- Referrer URL (die zuvor besuchte Seite)
- Hostname des zugreifenden Rechners
- Uhrzeit der Serveranfrage
- IP-Adresse

Eine Zusammenführung dieser Daten mit anderen Datenquellen wird nicht vorgenommen.

Die Erfassung dieser Daten erfolgt auf Grundlage von **Art. 6 Abs. 1 lit. f DSGVO**.
Der Websitebetreiber hat ein berechtigtes Interesse an der technisch fehlerfreien
Darstellung und der Optimierung seiner Website – hierzu müssen die Server-Logfiles
erfasst werden.

Die Daten werden nach {{ aufbewahrungsfrist|default('14 Tagen', true) }} gelöscht,
sofern keine längere Aufbewahrung zu Beweiszwecken erforderlich ist.
''',
    pflichtfelder=[],
)

# SSL/TLS Encryption
SSL_VERSCHLUESSELUNG = Baustein(
    id='ssl_verschluesselung',
    kategorie='basis',
    name='SSL-/TLS-Verschlüsselung',
    beschreibung='Hinweis auf verschlüsselte Datenübertragung',
    optional=False,
    order=20,
    text_template='''
### SSL- bzw. TLS-Verschlüsselung

Diese Seite nutzt aus Sicherheitsgründen und zum Schutz der Übertragung
vertraulicher Inhalte, wie zum Beispiel Anfragen, die Sie an uns als
Seitenbetreiber senden, eine SSL- bzw. TLS-Verschlüsselung.

Eine verschlüsselte Verbindung erkennen Sie daran, dass die Adresszeile des
Browsers von „http://" auf „https://" wechselt und an dem Schloss-Symbol in
Ihrer Browserzeile.

Wenn die SSL- bzw. TLS-Verschlüsselung aktiviert ist, können die Daten, die
Sie an uns übermitteln, nicht von Dritten mitgelesen werden.
''',
)

# Hosting Provider
HOSTING = Baustein(
    id='hosting',
    kategorie='basis',
    name='Hosting',
    beschreibung='Informationen zum Hosting-Anbieter',
    optional=True,
    order=30,
    pflichtfelder=['hosting_anbieter'],
    text_template='''
### Hosting

Unsere Website wird bei {{ hosting_anbieter }} gehostet. Der Hoster erhebt in
sogenannten Logfiles folgende Daten, die Ihr Browser übermittelt:

IP-Adresse, Datum und Uhrzeit der Anfrage, Zeitzonendifferenz zur Greenwich
Mean Time, Inhalt der Anforderung, HTTP-Statuscode, übertragene Datenmenge,
Website, von der die Anforderung kommt, und Informationen zu Browser und
Betriebssystem.

Das ist erforderlich, um unsere Website anzuzeigen und die Stabilität und
Sicherheit zu gewährleisten. Dies entspricht unserem berechtigten Interesse
im Sinne des **Art. 6 Abs. 1 lit. f DSGVO**.

{% if hosting_avv %}
Es besteht ein Vertrag über Auftragsverarbeitung (AVV) mit dem Hoster.
{% endif %}

{% if hosting_anbieter_adresse %}
**Anbieter:** {{ hosting_anbieter_adresse }}
{% endif %}
''',
)

# Technical Cookies
COOKIES_TECHNISCH = Baustein(
    id='cookies_technisch',
    kategorie='basis',
    name='Technisch notwendige Cookies',
    beschreibung='Cookies für Session-Management und Website-Funktion',
    optional=False,
    order=40,
    text_template='''
### Cookies

Unsere Website verwendet Cookies. Das sind kleine Textdateien, die Ihr
Webbrowser auf Ihrem Endgerät speichert.

**Technisch notwendige Cookies** helfen dabei, eine Website nutzbar zu machen,
indem sie Grundfunktionen wie Seitennavigation und Zugriff auf sichere Bereiche
der Website ermöglichen. Die Website kann ohne diese Cookies nicht richtig
funktionieren.

Diese Cookies werden auf Grundlage von **Art. 6 Abs. 1 lit. f DSGVO** gesetzt.
Wir haben ein berechtigtes Interesse an der Speicherung von Cookies zur technisch
fehlerfreien und optimierten Bereitstellung unserer Dienste.

Sie können Ihren Browser so einstellen, dass Sie über das Setzen von Cookies
informiert werden und Cookies nur im Einzelfall erlauben, die Annahme von
Cookies für bestimmte Fälle oder generell ausschließen sowie das automatische
Löschen der Cookies beim Schließen des Browsers aktivieren.

**Hinweis:** Bei der Deaktivierung von Cookies kann die Funktionalität dieser
Website eingeschränkt sein.
''',
)

# Betroffenenrechte (Rights of data subjects) - MANDATORY
BETROFFENENRECHTE = Baustein(
    id='betroffenenrechte',
    kategorie='basis',
    name='Betroffenenrechte',
    beschreibung='Hinweis auf Rechte der betroffenen Personen',
    optional=False,
    order=50,
    text_template='''
### Ihre Rechte als betroffene Person

Sie haben gegenüber uns folgende Rechte hinsichtlich der Sie betreffenden
personenbezogenen Daten:

- **Recht auf Auskunft** (Art. 15 DSGVO)
- **Recht auf Berichtigung** (Art. 16 DSGVO)
- **Recht auf Löschung** (Art. 17 DSGVO)
- **Recht auf Einschränkung der Verarbeitung** (Art. 18 DSGVO)
- **Recht auf Datenübertragbarkeit** (Art. 20 DSGVO)
- **Recht auf Widerspruch** gegen die Verarbeitung (Art. 21 DSGVO)

Sie haben zudem das Recht, sich bei einer **Datenschutz-Aufsichtsbehörde** über
die Verarbeitung Ihrer personenbezogenen Daten durch uns zu beschweren.

{% if aufsichtsbehoerde %}
Die für uns zuständige Aufsichtsbehörde ist:
{{ aufsichtsbehoerde }}
{% endif %}
''',
)

# Widerrufsrecht (Right to withdraw consent)
WIDERRUFSRECHT = Baustein(
    id='widerrufsrecht',
    kategorie='basis',
    name='Widerruf Ihrer Einwilligung',
    beschreibung='Hinweis auf Widerrufsrecht bei Einwilligungen',
    optional=False,
    order=60,
    text_template='''
### Widerruf Ihrer Einwilligung zur Datenverarbeitung

Viele Datenverarbeitungsvorgänge sind nur mit Ihrer ausdrücklichen Einwilligung
möglich. Sie können eine bereits erteilte Einwilligung jederzeit widerrufen.

Die Rechtmäßigkeit der bis zum Widerruf erfolgten Datenverarbeitung bleibt vom
Widerruf unberührt.

Für einen Widerruf genügt eine formlose Mitteilung per E-Mail an uns.
''',
)

# All basis Bausteine
BASIS_BAUSTEINE = [
    SERVER_LOGS,
    SSL_VERSCHLUESSELUNG,
    HOSTING,
    COOKIES_TECHNISCH,
    BETROFFENENRECHTE,
    WIDERRUFSRECHT,
]
