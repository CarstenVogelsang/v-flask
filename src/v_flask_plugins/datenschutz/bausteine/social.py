"""Social Media & Embeds Bausteine.

Text modules for YouTube, Google Maps, Google Fonts, and social media plugins.
"""

from v_flask_plugins.datenschutz.bausteine import Baustein

YOUTUBE = Baustein(
    id='youtube',
    kategorie='social',
    name='YouTube',
    beschreibung='Eingebettete YouTube-Videos',
    order=10,
    detect_patterns=[
        r'youtube\.com/embed',
        r'youtube-nocookie\.com',
        r'youtu\.be',
        r'ytimg\.com',
    ],
    text_template='''
### YouTube

Unsere Website nutzt Plugins der von Google betriebenen Seite YouTube.
Betreiber der Seiten ist die Google Ireland Limited („Google"), Gordon House,
Barrow Street, Dublin 4, Irland.

{% if youtube_nocookie %}
Wir nutzen YouTube im erweiterten Datenschutzmodus. Dieser Modus bewirkt laut
YouTube, dass YouTube keine Informationen über die Besucher auf dieser Website
speichert, bevor diese sich das Video ansehen.
{% endif %}

Wenn Sie eine unserer Seiten mit YouTube-Plugin besuchen, wird eine Verbindung
zu den Servern von YouTube hergestellt. Dabei wird dem YouTube-Server mitgeteilt,
welche unserer Seiten Sie besucht haben.

Wenn Sie in Ihrem YouTube-Account eingeloggt sind, ermöglichen Sie YouTube,
Ihr Surfverhalten direkt Ihrem persönlichen Profil zuzuordnen. Dies können Sie
verhindern, indem Sie sich aus Ihrem YouTube-Account ausloggen.

Die Nutzung von YouTube erfolgt im Interesse einer ansprechenden Darstellung
unserer Online-Angebote. Dies stellt ein berechtigtes Interesse gemäß
**Art. 6 Abs. 1 lit. f DSGVO** dar. Sofern eine entsprechende Einwilligung
abgefragt wurde, erfolgt die Verarbeitung gemäß **Art. 6 Abs. 1 lit. a DSGVO**.

Weitere Informationen zum Umgang mit Nutzerdaten finden Sie in der
Datenschutzerklärung von YouTube:
[https://policies.google.com/privacy](https://policies.google.com/privacy)
''',
)

GOOGLE_MAPS = Baustein(
    id='google_maps',
    kategorie='social',
    name='Google Maps',
    beschreibung='Eingebettete Google Maps Karten',
    order=20,
    detect_patterns=[
        r'maps\.googleapis\.com',
        r'google\.com/maps',
        r'maps\.google\.com',
    ],
    text_template='''
### Google Maps

Diese Website nutzt den Kartendienst Google Maps. Anbieter ist die Google
Ireland Limited („Google"), Gordon House, Barrow Street, Dublin 4, Irland.

Zur Nutzung der Funktionen von Google Maps ist es notwendig, Ihre IP-Adresse
zu speichern. Diese Informationen werden in der Regel an einen Server von
Google in den USA übertragen und dort gespeichert.

Die Nutzung von Google Maps erfolgt im Interesse einer ansprechenden Darstellung
unserer Online-Angebote und an einer leichten Auffindbarkeit der von uns auf der
Website angegebenen Orte. Dies stellt ein berechtigtes Interesse gemäß
**Art. 6 Abs. 1 lit. f DSGVO** dar. Sofern eine entsprechende Einwilligung
abgefragt wurde, erfolgt die Verarbeitung gemäß **Art. 6 Abs. 1 lit. a DSGVO**.

Mehr Informationen zum Umgang mit Nutzerdaten finden Sie in der
Datenschutzerklärung von Google:
[https://policies.google.com/privacy](https://policies.google.com/privacy)
''',
)

GOOGLE_FONTS = Baustein(
    id='google_fonts',
    kategorie='social',
    name='Google Fonts',
    beschreibung='Schriftarten von Google Fonts',
    order=30,
    detect_patterns=[r'fonts\.googleapis\.com', r'fonts\.gstatic\.com'],
    text_template='''
### Google Fonts

Diese Seite nutzt zur einheitlichen Darstellung von Schriftarten sogenannte
Google Fonts, die von Google bereitgestellt werden.

{% if google_fonts_lokal %}
Die Google Fonts sind lokal installiert. Eine Verbindung zu Servern von
Google findet dabei nicht statt.
{% else %}
Beim Aufruf einer Seite lädt Ihr Browser die benötigten Fonts in Ihren
Browsercache, um Texte und Schriftarten korrekt anzuzeigen. Zu diesem Zweck
muss der von Ihnen verwendete Browser Verbindung zu den Servern von Google
aufnehmen. Hierdurch erlangt Google Kenntnis darüber, dass über Ihre IP-Adresse
diese Website aufgerufen wurde.
{% endif %}

Die Nutzung von Google Fonts erfolgt auf Grundlage von **Art. 6 Abs. 1 lit. f DSGVO**.
Wir haben ein berechtigtes Interesse an der einheitlichen Darstellung des
Schriftbildes auf unserer Website. Sofern eine entsprechende Einwilligung
abgefragt wurde, erfolgt die Verarbeitung gemäß **Art. 6 Abs. 1 lit. a DSGVO**.

Weitere Informationen zu Google Fonts finden Sie unter:
[https://fonts.google.com/](https://fonts.google.com/)
''',
)

FACEBOOK_PIXEL = Baustein(
    id='facebook_pixel',
    kategorie='social',
    name='Facebook/Meta Pixel',
    beschreibung='Facebook/Meta Tracking Pixel',
    order=40,
    detect_patterns=[r'connect\.facebook\.net', r'fbq\(', r'facebook\.com/tr'],
    pflichtfelder=['facebook_pixel_id'],
    text_template='''
### Meta-Pixel (Facebook Pixel)

Wir nutzen auf unserer Website das Meta-Pixel (Facebook Pixel) von Meta
Platforms Ireland Limited, 4 Grand Canal Square, Dublin 2, Irland.

Mit Hilfe des Meta-Pixels können wir die Besucher unserer Website nach dem
Weiterleiten auf Facebook als Zielgruppe für die Darstellung von Anzeigen
(Facebook-Ads) bestimmen.

{% if facebook_pixel_id %}
Pixel-ID: **{{ facebook_pixel_id }}**
{% endif %}

Die Verarbeitung der Daten durch Meta erfolgt im Rahmen von Metas
Datenverwendungsrichtlinie. Die Rechtsgrundlage für die Nutzung des Meta-Pixels
ist Ihre Einwilligung gemäß **Art. 6 Abs. 1 lit. a DSGVO**.

Informationen zu den Einstellungsmöglichkeiten für Werbeanzeigen finden Sie bei
Facebook unter:
[https://www.facebook.com/settings?tab=ads](https://www.facebook.com/settings?tab=ads)
''',
)

TWITTER = Baustein(
    id='twitter',
    kategorie='social',
    name='Twitter / X',
    beschreibung='Twitter/X Plugins und Widgets',
    order=50,
    detect_patterns=[r'platform\.twitter\.com', r'twitter\.com/widgets'],
    text_template='''
### Twitter / X

Auf unserer Website sind Funktionen des Dienstes X (ehemals Twitter) eingebunden.
Diese Funktionen werden angeboten durch die X Corp., 1355 Market Street, Suite 900,
San Francisco, CA 94103, USA.

Wenn Sie X und die Funktion „Re-Tweet" nutzen, werden die von Ihnen besuchten
Websites mit Ihrem X-Account verknüpft und anderen Nutzern bekannt gegeben.
Dabei werden auch Daten an X übertragen.

Die Nutzung erfolgt auf Grundlage Ihrer Einwilligung gemäß **Art. 6 Abs. 1 lit. a DSGVO**.

Weitere Informationen finden Sie in der Datenschutzerklärung von X:
[https://twitter.com/privacy](https://twitter.com/privacy)
''',
)

INSTAGRAM = Baustein(
    id='instagram',
    kategorie='social',
    name='Instagram',
    beschreibung='Instagram Plugins und Embeds',
    order=60,
    detect_patterns=[r'instagram\.com/embed', r'cdninstagram\.com'],
    text_template='''
### Instagram

Auf unserer Website sind Funktionen des Dienstes Instagram eingebunden.
Instagram gehört zu Meta Platforms Ireland Limited, 4 Grand Canal Square,
Dublin 2, Irland.

Wenn Sie auf unserer Website Inhalte von Instagram sehen oder mit
Instagram-Funktionen interagieren, wird eine Verbindung zu den Servern von
Instagram hergestellt. Dabei werden Daten an Instagram übermittelt.

Die Nutzung erfolgt auf Grundlage unseres berechtigten Interesses an einer
ansprechenden Darstellung unserer Website gemäß **Art. 6 Abs. 1 lit. f DSGVO**
oder auf Grundlage Ihrer Einwilligung gemäß **Art. 6 Abs. 1 lit. a DSGVO**.

Weitere Informationen finden Sie in der Datenschutzerklärung von Instagram:
[https://help.instagram.com/519522125107875](https://help.instagram.com/519522125107875)
''',
)

SOCIAL_BAUSTEINE = [
    YOUTUBE,
    GOOGLE_MAPS,
    GOOGLE_FONTS,
    FACEBOOK_PIXEL,
    TWITTER,
    INSTAGRAM,
]
