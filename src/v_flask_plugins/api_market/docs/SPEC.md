# API Market Plugin - Spezifikation

## Übersicht

Das API Market Plugin bietet einen internen API-Marketplace mit automatischer Dokumentation aus OpenAPI-Specs, API-Key-Management und Code-Beispiel-Generierung in mehreren Programmiersprachen.

## Zielgruppe

- **Admins**: Verwaltung registrierter APIs
- **Entwickler/Partner**: API-Dokumentation und Code-Beispiele nutzen
- **API-Anbieter**: Nutzungsstatistiken einsehen

## User Stories

- Als Admin möchte ich externe APIs registrieren, damit sie dokumentiert werden
- Als Entwickler möchte ich API-Dokumentation mit Code-Beispielen sehen
- Als Partner möchte ich API-Keys für den Zugang erhalten
- Als Admin möchte ich API-Nutzung tracken

## Funktionale Anforderungen

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | APIs aus OpenAPI-Specs registrieren | Must | POC |
| F2 | Automatische Dokumentation generieren | Must | POC |
| F3 | Code-Beispiele (Python) | Must | MVP |
| F4 | Code-Beispiele (C#, Delphi) | Should | MVP |
| F5 | Spec-Caching | Should | MVP |
| F6 | API-Key Management | Could | V1 |
| F7 | Usage-Tracking | Could | V1 |

## Code-Beispiel-Sprachen

| Sprache | Library | Beispiel |
|---------|---------|----------|
| Python | requests | `requests.get(url, headers={...})` |
| C# | HttpClient | `await client.GetAsync(url)` |
| Delphi | Indy | `IdHTTP.Get(url)` |

## Nicht-funktionale Anforderungen

- **Performance**: Specs werden gecached (default 1h)
- **Verfügbarkeit**: Fallback wenn externe API nicht erreichbar
- **Sicherheit**: Admin-only für API-Verwaltung

## Abgrenzung (Out of Scope)

- API-Proxy (direktes Weiterleiten von Anfragen)
- Rate-Limiting
- Billing/Abrechnung
