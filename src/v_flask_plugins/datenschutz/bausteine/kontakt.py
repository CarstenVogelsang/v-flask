"""Kontakt & Kommunikation Bausteine.

Text modules for contact forms, email communication, and phone contact.
"""

from v_flask_plugins.datenschutz.bausteine import Baustein

KONTAKTFORMULAR = Baustein(
    id='kontaktformular',
    kategorie='kontakt',
    name='Kontaktformular',
    beschreibung='Datenverarbeitung bei Kontaktanfragen über Webformular',
    order=10,
    detect_plugins=['kontakt'],  # Auto-detect when Kontakt plugin is active
    text_template='''
### Kontaktformular

Wenn Sie uns per Kontaktformular Anfragen zukommen lassen, werden Ihre Angaben
aus dem Anfrageformular inklusive der von Ihnen dort angegebenen Kontaktdaten
zwecks Bearbeitung der Anfrage und für den Fall von Anschlussfragen bei uns
gespeichert.

Die Verarbeitung dieser Daten erfolgt auf Grundlage von **Art. 6 Abs. 1 lit. b DSGVO**,
sofern Ihre Anfrage mit der Erfüllung eines Vertrags zusammenhängt oder zur
Durchführung vorvertraglicher Maßnahmen erforderlich ist. In allen übrigen Fällen
beruht die Verarbeitung auf unserem berechtigten Interesse an der effektiven
Bearbeitung der an uns gerichteten Anfragen (**Art. 6 Abs. 1 lit. f DSGVO**) oder
auf Ihrer Einwilligung (**Art. 6 Abs. 1 lit. a DSGVO**), sofern diese abgefragt wurde.

Die von Ihnen im Kontaktformular eingegebenen Daten verbleiben bei uns, bis Sie
uns zur Löschung auffordern, Ihre Einwilligung zur Speicherung widerrufen oder
der Zweck für die Datenspeicherung entfällt. Zwingende gesetzliche Bestimmungen
– insbesondere Aufbewahrungsfristen – bleiben unberührt.
''',
)

EMAIL_KOMMUNIKATION = Baustein(
    id='email_kommunikation',
    kategorie='kontakt',
    name='Anfrage per E-Mail',
    beschreibung='Datenverarbeitung bei E-Mail-Anfragen',
    order=20,
    text_template='''
### Anfrage per E-Mail

Wenn Sie uns per E-Mail kontaktieren, wird Ihre Anfrage inklusive aller daraus
hervorgehenden personenbezogenen Daten (Name, Anfrage) zum Zwecke der Bearbeitung
Ihres Anliegens bei uns gespeichert und verarbeitet.

Die Verarbeitung dieser Daten erfolgt auf Grundlage von **Art. 6 Abs. 1 lit. b DSGVO**,
sofern Ihre Anfrage mit der Erfüllung eines Vertrags zusammenhängt oder zur
Durchführung vorvertraglicher Maßnahmen erforderlich ist. In allen übrigen Fällen
beruht die Verarbeitung auf Ihrer Einwilligung (**Art. 6 Abs. 1 lit. a DSGVO**)
und/oder auf unseren berechtigten Interessen (**Art. 6 Abs. 1 lit. f DSGVO**).

Die von Ihnen an uns per E-Mail gesandten Daten verbleiben bei uns, bis Sie uns
zur Löschung auffordern, Ihre Einwilligung zur Speicherung widerrufen oder der
Zweck für die Datenspeicherung entfällt.
''',
)

TELEFON = Baustein(
    id='telefon',
    kategorie='kontakt',
    name='Anfrage per Telefon',
    beschreibung='Datenverarbeitung bei telefonischen Anfragen',
    order=30,
    text_template='''
### Anfrage per Telefon

Wenn Sie uns per Telefon kontaktieren, wird Ihre Anfrage inklusive aller daraus
hervorgehenden personenbezogenen Daten (Name, Anfrage, ggf. Telefonnummer) zum
Zwecke der Bearbeitung Ihres Anliegens bei uns gespeichert und verarbeitet.

Die Verarbeitung dieser Daten erfolgt auf Grundlage von **Art. 6 Abs. 1 lit. b DSGVO**,
sofern Ihre Anfrage mit der Erfüllung eines Vertrags zusammenhängt. In allen
übrigen Fällen beruht die Verarbeitung auf Ihrer Einwilligung und/oder auf
unseren berechtigten Interessen an einer effektiven Bearbeitung der an uns
gerichteten Anfragen.
''',
)

KONTAKT_BAUSTEINE = [
    KONTAKTFORMULAR,
    EMAIL_KOMMUNIKATION,
    TELEFON,
]
