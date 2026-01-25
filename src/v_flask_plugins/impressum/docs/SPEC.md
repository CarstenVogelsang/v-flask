# Impressum Plugin - Spezifikation

## Übersicht

Das Impressum Plugin generiert ein gesetzeskonformes deutsches Impressum nach § 5 TMG aus strukturierten Betreiberdaten mit Admin-Editor, Live-Vorschau und Validierung der Pflichtangaben.

## Zielgruppe

- **Admins**: Konfiguration des Impressums im Backend
- **Website-Besucher**: Einsicht in Pflichtangaben des Anbieters

## User Stories

- Als Admin möchte ich mein Impressum über ein Formular erstellen, damit ich keine rechtlichen Fehler mache
- Als Admin möchte ich Warnungen sehen wenn Pflichtangaben fehlen, damit ich compliant bleibe
- Als Besucher möchte ich das Impressum einsehen, um den Anbieter zu identifizieren

## Funktionale Anforderungen

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | Impressum aus Betreiberdaten generieren | Must | POC |
| F2 | Admin-Editor mit strukturierter Eingabe | Must | POC |
| F3 | Live-Vorschau im Admin | Must | MVP |
| F4 | Validierung der Pflichtangaben | Must | MVP |
| F5 | Toggle für V.i.S.d.P. | Should | MVP |
| F6 | Toggle für Streitschlichtung | Should | MVP |
| F7 | Eigener Disclaimer | Should | V1 |

## Pflichtangaben nach § 5 TMG

| Angabe | Pflicht | Hinweis |
|--------|---------|---------|
| Name | Ja | Vollständiger Name/Firma |
| Anschrift | Ja | Straße, PLZ, Ort |
| E-Mail | Ja | Schnelle Kontaktaufnahme |
| Vertretungsberechtigter | Bei jur. Personen | Geschäftsführer |
| Handelsregister | Falls vorhanden | Registergericht + Nummer |
| USt-IdNr. | Falls vorhanden | Bei wirtschaftlicher Tätigkeit |

## Nicht-funktionale Anforderungen

- **Compliance**: Erfüllt Anforderungen nach § 5 TMG
- **Sicherheit**: Nur Admin-Zugriff auf Editor
- **UX**: Klare Validierungsmeldungen

## Abgrenzung (Out of Scope)

- Automatische Erkennung der Rechtsform
- Multi-Language Impressum
- PDF-Export
