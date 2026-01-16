"""Analytics & Tracking Bausteine.

Text modules for analytics services like Google Analytics, Matomo, etc.
"""

from v_flask_plugins.datenschutz.bausteine import Baustein

GOOGLE_ANALYTICS = Baustein(
    id='google_analytics',
    kategorie='analytics',
    name='Google Analytics',
    beschreibung='Google Analytics 4 (GA4) Tracking',
    order=10,
    detect_patterns=[r'gtag\(', r'G-[A-Z0-9]+', r'googletagmanager\.com'],
    pflichtfelder=['tracking_id'],
    text_template='''
### Google Analytics

Diese Website benutzt Google Analytics, einen Webanalysedienst der Google Ireland
Limited („Google"), Gordon House, Barrow Street, Dublin 4, Irland.

Google Analytics verwendet sogenannte „Cookies", Textdateien, die auf Ihrem
Computer gespeichert werden und die eine Analyse der Benutzung der Website
durch Sie ermöglichen.

{% if tracking_id %}
Wir nutzen Google Analytics mit der Mess-ID: **{{ tracking_id }}**
{% endif %}

Die durch das Cookie erzeugten Informationen über Ihre Benutzung dieser Website
werden in der Regel an einen Server von Google in den USA übertragen und dort
gespeichert.

**IP-Anonymisierung:** Wir haben auf dieser Website die Funktion IP-Anonymisierung
aktiviert. Dadurch wird Ihre IP-Adresse von Google innerhalb von Mitgliedstaaten
der Europäischen Union oder in anderen Vertragsstaaten des Abkommens über den
Europäischen Wirtschaftsraum vor der Übermittlung in die USA gekürzt.

Die Nutzung dieses Analyse-Dienstes erfolgt auf Grundlage Ihrer Einwilligung
gemäß **Art. 6 Abs. 1 lit. a DSGVO**. Sie können Ihre Einwilligung jederzeit
widerrufen.

**Opt-Out:** Sie können die Speicherung der Cookies durch eine entsprechende
Einstellung Ihrer Browser-Software verhindern. Sie können darüber hinaus die
Erfassung der durch das Cookie erzeugten Daten durch Google verhindern, indem
Sie das unter dem folgenden Link verfügbare Browser-Plugin herunterladen und
installieren: [https://tools.google.com/dlpage/gaoptout](https://tools.google.com/dlpage/gaoptout)

Weitere Informationen zum Umgang mit Nutzerdaten bei Google Analytics finden Sie
in der Datenschutzerklärung von Google:
[https://support.google.com/analytics/answer/6004245](https://support.google.com/analytics/answer/6004245)
''',
)

MATOMO = Baustein(
    id='matomo',
    kategorie='analytics',
    name='Matomo',
    beschreibung='Matomo (ehemals Piwik) Webanalyse',
    order=20,
    detect_patterns=[r'matomo\.js', r'piwik\.js', r'_paq\.push'],
    pflichtfelder=['matomo_url'],
    text_template='''
### Matomo (ehemals Piwik)

Diese Website nutzt den Webanalysedienst Matomo zur Analyse und Optimierung
unserer Website. Matomo ist eine Open-Source-Software.

{% if matomo_selbst_gehostet %}
Matomo wird auf unseren eigenen Servern gehostet, sodass keine Daten an
Dritte übermittelt werden.
{% else %}
Matomo-Server: {{ matomo_url|default('Selbst gehostet', true) }}
{% endif %}

Durch die Analyse können wir unser Angebot fortlaufend verbessern. Die
Rechtsgrundlage für die Nutzung dieses Analyse-Dienstes ist **Art. 6 Abs. 1 lit. f DSGVO**.
Wir haben ein berechtigtes Interesse an der Analyse des Nutzerverhaltens zur
Optimierung unserer Website.

Die IP-Adresse wird vor der Speicherung anonymisiert, sodass keine Rückschlüsse
auf einzelne Nutzer möglich sind.

**Opt-Out:** Sie können der Datenerhebung widersprechen, indem Sie die
Do-Not-Track-Einstellung Ihres Browsers aktivieren.
''',
)

HOTJAR = Baustein(
    id='hotjar',
    kategorie='analytics',
    name='Hotjar',
    beschreibung='Hotjar Heatmaps und Session Recordings',
    order=30,
    detect_patterns=[r'hotjar\.com', r'hj\(', r'hjid'],
    text_template='''
### Hotjar

Wir nutzen Hotjar, um die Bedürfnisse unserer Nutzer besser zu verstehen und
das Angebot auf dieser Website zu optimieren. Anbieter ist die Hotjar Ltd.,
Level 2, St Julian's Business Centre, 3, Elia Zammit Street, St Julian's STJ 1000, Malta.

Mit Hilfe von Hotjar können wir das Nutzungsverhalten (Mausbewegungen, Klicks,
Scrolltiefe usw.) auf unserer Website analysieren. Die Rechtsgrundlage für die
Verarbeitung ist Ihre Einwilligung gemäß **Art. 6 Abs. 1 lit. a DSGVO**.

Hotjar verwendet Cookies und andere Technologien, um Informationen über das
Verhalten unserer Nutzer und über deren Endgeräte zu sammeln. Dabei werden
keine personenbezogenen Daten erhoben; die IP-Adresse wird anonymisiert.

**Opt-Out:** Sie können die Erfassung durch Hotjar verhindern, indem Sie auf
folgenden Link klicken und die dortigen Anweisungen befolgen:
[https://www.hotjar.com/opt-out](https://www.hotjar.com/opt-out)
''',
)

TRACKING_ALLGEMEIN = Baustein(
    id='tracking_allgemein',
    kategorie='analytics',
    name='Allgemeiner Tracking-Hinweis',
    beschreibung='Generischer Hinweis auf Webanalyse',
    order=100,
    text_template='''
### Webanalyse

Diese Website verwendet Webanalyse-Tools zur statistischen Auswertung der
Besucherzugriffe. Die dabei erhobenen Daten werden nicht dazu benutzt, den
Besucher dieser Website persönlich zu identifizieren.

Die Nutzung erfolgt auf Grundlage unseres berechtigten Interesses an einer
statistischen Analyse des Nutzerverhaltens zu Optimierungszwecken gemäß
**Art. 6 Abs. 1 lit. f DSGVO** oder auf Grundlage Ihrer Einwilligung gemäß
**Art. 6 Abs. 1 lit. a DSGVO**, sofern diese abgefragt wurde.
''',
)

ANALYTICS_BAUSTEINE = [
    GOOGLE_ANALYTICS,
    MATOMO,
    HOTJAR,
    TRACKING_ALLGEMEIN,
]
