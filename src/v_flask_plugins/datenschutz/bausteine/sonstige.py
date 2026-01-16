"""Sonstige Bausteine.

Text modules for CDNs, captchas, login systems, and comments.
"""

from v_flask_plugins.datenschutz.bausteine import Baustein

CDN = Baustein(
    id='cdn',
    kategorie='sonstige',
    name='Content Delivery Networks (CDN)',
    beschreibung='Nutzung von CDNs für schnellere Ladezeiten',
    order=10,
    detect_patterns=[
        r'cdnjs\.cloudflare\.com',
        r'cdn\.jsdelivr\.net',
        r'unpkg\.com',
        r'bootstrapcdn\.com',
    ],
    pflichtfelder=['cdn_anbieter'],
    text_template='''
### Content Delivery Networks (CDN)

Um die Ladegeschwindigkeit unserer Website zu verbessern, nutzen wir ein
Content Delivery Network (CDN).

{% if cdn_anbieter %}
Wir nutzen das CDN von: **{{ cdn_anbieter }}**
{% endif %}

Beim Aufruf unserer Website werden Dateien wie JavaScript-Bibliotheken oder
CSS-Frameworks von Servern des CDN-Anbieters geladen. Dabei wird Ihre IP-Adresse
an den CDN-Anbieter übermittelt.

Die Nutzung erfolgt auf Grundlage unseres berechtigten Interesses an einer
schnellen und sicheren Bereitstellung unserer Website gemäß
**Art. 6 Abs. 1 lit. f DSGVO**.
''',
)

RECAPTCHA = Baustein(
    id='recaptcha',
    kategorie='sonstige',
    name='Google reCAPTCHA',
    beschreibung='Schutz vor Spam und Bots',
    order=20,
    detect_patterns=[r'google\.com/recaptcha', r'recaptcha', r'grecaptcha'],
    text_template='''
### Google reCAPTCHA

Wir nutzen „Google reCAPTCHA" (im Folgenden „reCAPTCHA") auf dieser Website.
Anbieter ist die Google Ireland Limited („Google"), Gordon House, Barrow Street,
Dublin 4, Irland.

Mit reCAPTCHA soll überprüft werden, ob die Dateneingabe auf dieser Website
(z.B. in einem Kontaktformular) durch einen Menschen oder durch ein
automatisiertes Programm erfolgt.

Hierzu analysiert reCAPTCHA das Verhalten des Websitebesuchers anhand
verschiedener Merkmale. Diese Analyse beginnt automatisch, sobald der
Websitebesucher die Website betritt. Zur Analyse wertet reCAPTCHA verschiedene
Informationen aus (z.B. IP-Adresse, Verweildauer des Websitebesuchers auf der
Website oder vom Nutzer getätigte Mausbewegungen).

Die Nutzung von reCAPTCHA erfolgt auf Grundlage von **Art. 6 Abs. 1 lit. f DSGVO**.
Wir haben ein berechtigtes Interesse daran, unsere Webangebote vor missbräuchlicher
automatisierter Ausspähung und vor Spam zu schützen.

Weitere Informationen zu Google reCAPTCHA finden Sie unter:
[https://policies.google.com/privacy](https://policies.google.com/privacy)
''',
)

HCAPTCHA = Baustein(
    id='hcaptcha',
    kategorie='sonstige',
    name='hCaptcha',
    beschreibung='Schutz vor Spam und Bots (Alternative zu reCAPTCHA)',
    order=25,
    detect_patterns=[r'hcaptcha\.com', r'hcaptcha'],
    text_template='''
### hCaptcha

Wir nutzen hCaptcha als Schutz vor Spam und Bots. Anbieter ist die Intuition
Machines, Inc., 350 Alabama St, San Francisco, CA 94110, USA.

hCaptcha wird eingesetzt, um zu überprüfen, ob die Dateneingabe auf dieser
Website durch einen Menschen oder durch ein automatisiertes Programm erfolgt.

Bei der Nutzung von hCaptcha werden Daten über Ihr Nutzungsverhalten
(z.B. Mausbewegungen, IP-Adresse) an hCaptcha übermittelt.

Die Nutzung von hCaptcha erfolgt auf Grundlage von **Art. 6 Abs. 1 lit. f DSGVO**.
Wir haben ein berechtigtes Interesse daran, unsere Webangebote vor
missbräuchlicher automatisierter Nutzung zu schützen.

Die Datenschutzerklärung von hCaptcha finden Sie unter:
[https://www.hcaptcha.com/privacy](https://www.hcaptcha.com/privacy)
''',
)

LOGIN = Baustein(
    id='login',
    kategorie='sonstige',
    name='Benutzerregistrierung / Login',
    beschreibung='Nutzerkonto und Anmeldung',
    order=30,
    text_template='''
### Benutzerregistrierung und Login

Sie können sich auf unserer Website registrieren, um zusätzliche Funktionen
zu nutzen. Die dazu eingegebenen Daten verwenden wir nur zum Zwecke der Nutzung
des jeweiligen Angebotes, für das Sie sich registriert haben.

Die bei der Registrierung abgefragten Pflichtangaben müssen vollständig angegeben
werden. Anderenfalls werden wir die Registrierung ablehnen.

Für wichtige Änderungen etwa beim Angebotsumfang oder bei technisch notwendigen
Änderungen nutzen wir die bei der Registrierung angegebene E-Mail-Adresse.

Die Verarbeitung der bei der Registrierung eingegebenen Daten erfolgt auf
Grundlage Ihrer Einwilligung (**Art. 6 Abs. 1 lit. a DSGVO**) oder zur Erfüllung
eines Vertrages (**Art. 6 Abs. 1 lit. b DSGVO**).

Die während der Registrierung gespeicherten Daten werden von uns gespeichert,
solange Sie auf unserer Website registriert sind, und werden anschließend gelöscht.
Gesetzliche Aufbewahrungsfristen bleiben unberührt.
''',
)

KOMMENTARE = Baustein(
    id='kommentare',
    kategorie='sonstige',
    name='Kommentarfunktion',
    beschreibung='Kommentare auf der Website',
    order=40,
    text_template='''
### Kommentarfunktion

Wenn Nutzer Kommentare auf unserer Website hinterlassen, werden neben dem
Kommentar selbst auch Angaben zum Zeitpunkt der Erstellung des Kommentars,
die E-Mail-Adresse und, wenn nicht anonym kommentiert wird, der gewählte
Nutzername gespeichert.

Die IP-Adresse wird mitgespeichert, um die Zuordnung eines Kommentars zu einem
Nutzer zu ermöglichen und um gegen die Verbreitung rechtswidriger Inhalte
vorgehen zu können.

Die Speicherung erfolgt auf Grundlage unserer berechtigten Interessen gemäß
**Art. 6 Abs. 1 lit. f DSGVO**. Wir sind an der ordnungsgemäßen Verwaltung der
Kommentarfunktion und am Schutz vor rechtswidrigen Inhalten interessiert.

Die Kommentare und die damit verbundenen Daten werden gespeichert und verbleiben
auf unserer Website, bis der kommentierte Inhalt vollständig gelöscht wurde oder
die Kommentare aus rechtlichen Gründen gelöscht werden müssen.
''',
)

SONSTIGE_BAUSTEINE = [
    CDN,
    RECAPTCHA,
    HCAPTCHA,
    LOGIN,
    KOMMENTARE,
]
