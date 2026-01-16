"""Marketing Bausteine.

Text modules for newsletters, advertising, and remarketing.
"""

from v_flask_plugins.datenschutz.bausteine import Baustein

NEWSLETTER = Baustein(
    id='newsletter',
    kategorie='marketing',
    name='Newsletter',
    beschreibung='E-Mail Newsletter-Anmeldung',
    order=10,
    detect_plugins=['newsletter'],
    pflichtfelder=['newsletter_anbieter'],
    text_template='''
### Newsletter

Wenn Sie den auf der Website angebotenen Newsletter beziehen möchten, benötigen
wir von Ihnen eine E-Mail-Adresse sowie Informationen, welche uns die Überprüfung
gestatten, dass Sie der Inhaber der angegebenen E-Mail-Adresse sind und mit dem
Empfang des Newsletters einverstanden sind.

{% if newsletter_anbieter %}
Für den Versand unseres Newsletters nutzen wir **{{ newsletter_anbieter }}**.
{% endif %}

{% if newsletter_double_optin %}
Wir setzen das sogenannte Double-Opt-In-Verfahren ein. Nach Ihrer Anmeldung
erhalten Sie eine E-Mail, in der Sie um die Bestätigung Ihrer Anmeldung
gebeten werden.
{% endif %}

Die von Ihnen zum Zwecke des Newsletter-Bezugs bei uns hinterlegten Daten werden
von uns bis zu Ihrer Austragung aus dem Newsletter gespeichert und nach der
Abbestellung des Newsletters gelöscht.

Die Rechtsgrundlage für die Verarbeitung ist Ihre Einwilligung gemäß
**Art. 6 Abs. 1 lit. a DSGVO**.

Die erteilte Einwilligung zur Speicherung der Daten, der E-Mail-Adresse sowie
deren Nutzung zum Versand des Newsletters können Sie jederzeit widerrufen,
etwa über den „Abmelden"-Link im Newsletter.
''',
)

WERBUNG = Baustein(
    id='werbung',
    kategorie='marketing',
    name='Werbung',
    beschreibung='Werbenetzwerke und personalisierte Werbung',
    order=20,
    detect_patterns=[r'googlesyndication\.com', r'doubleclick\.net', r'adsense'],
    text_template='''
### Werbung

Diese Website nutzt Werbenetzwerke zur Einblendung von Werbeanzeigen. Dabei
können Cookies eingesetzt werden, die es ermöglichen, Ihnen personalisierte
Werbung anzuzeigen.

Die Nutzung von Werbediensten erfolgt auf Grundlage Ihrer Einwilligung gemäß
**Art. 6 Abs. 1 lit. a DSGVO**.

Sie können der Verwendung von Cookies für personalisierte Werbung über folgende
Seiten widersprechen:
- [https://www.youronlinechoices.com/](https://www.youronlinechoices.com/)
- [https://optout.networkadvertising.org/](https://optout.networkadvertising.org/)
''',
)

REMARKETING = Baustein(
    id='remarketing',
    kategorie='marketing',
    name='Remarketing / Retargeting',
    beschreibung='Remarketing-Dienste für zielgerichtete Werbung',
    order=30,
    detect_patterns=[r'googleadservices\.com', r'criteo\.com', r'adroll\.com'],
    pflichtfelder=['remarketing_dienst'],
    text_template='''
### Remarketing / Retargeting

Diese Website nutzt Remarketing-Funktionen. Remarketing ermöglicht es,
Besuchern unserer Website zielgerichtete Werbung auf anderen Websites
anzuzeigen.

{% if remarketing_dienst %}
Wir nutzen den Remarketing-Dienst: **{{ remarketing_dienst }}**
{% endif %}

Beim Besuch unserer Website wird ein Remarketing-Cookie auf Ihrem Computer
gesetzt. Dieses Cookie ermöglicht es, Sie auf anderen Websites wiederzuerkennen
und Ihnen interessenbasierte Werbung zu zeigen.

Die Rechtsgrundlage für die Verarbeitung ist Ihre Einwilligung gemäß
**Art. 6 Abs. 1 lit. a DSGVO**.

Sie können die personalisierte Werbung in den Einstellungen Ihres Browsers
oder auf folgenden Seiten deaktivieren:
- [https://adssettings.google.com/](https://adssettings.google.com/)
- [https://www.youronlinechoices.com/](https://www.youronlinechoices.com/)
''',
)

MARKETING_BAUSTEINE = [
    NEWSLETTER,
    WERBUNG,
    REMARKETING,
]
