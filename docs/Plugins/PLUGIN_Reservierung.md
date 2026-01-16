# Reservierungs-Integration für fruehstuecken.click — V2


## Strategische Positionierung

### Zwei-Säulen-Modell

Das Verzeichnis bietet **zwei parallele Wege** für Reservierungen:

| Säule | Beschreibung | Zielgruppe |
|-------|--------------|------------|
| **Option A: Externe Anbindung** | Verweis auf bestehendes System des Betreibers | Lokale mit vorhandenem System |
| **Option C: Eigenes System** | Integriertes Reservierungs-Plugin | Lokale ohne System / Wechselwillige |

**Vorteile des Parallelangebots:**
- Keine Einstiegshürde für Betreiber mit bestehendem System
- Sanfter Migrationspfad zu Option C
- Datensammlung über Marktverteilung (welche Systeme werden genutzt?)
- Vertriebsargument: "Wir integrieren uns, statt zu ersetzen"

---

## Option A: Externe System-Anbindung

### Konzept

Betreiber können ihr bestehendes Reservierungssystem verknüpfen. Statt einer einfachen URL-Eingabe erfassen wir **strukturierte Daten** über das genutzte System.

### Datenmodell-Erweiterung

```sql
-- Externe Reservierungssysteme (Stammdaten)
CREATE TABLE external_reservation_systems (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,        -- 'thefork', 'opentable', 'resmio', 'eigen', 'telefon', 'whatsapp'
  name TEXT NOT NULL,               -- 'TheFork', 'OpenTable', 'resmio', 'Eigene Website', 'Nur Telefon', 'WhatsApp'
  icon TEXT,                        -- Icon-Referenz (Tabler oder Custom)
  base_url_pattern TEXT,            -- z.B. 'https://www.thefork.de/restaurant/{slug}'
  is_active BOOLEAN DEFAULT true,
  display_order INT DEFAULT 0
);

-- Zuordnung Location → Externes System
CREATE TABLE location_external_reservations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  location_id UUID REFERENCES locations(id) ON DELETE CASCADE,
  system_id UUID REFERENCES external_reservation_systems(id),
  
  -- Verbindungsdaten
  external_url TEXT,                -- Vollständige URL zur Reservierungsseite
  external_identifier TEXT,         -- z.B. TheFork-Restaurant-ID, falls bekannt
  phone_number TEXT,                -- Falls System = 'telefon' oder 'whatsapp'
  
  -- Meta
  is_primary BOOLEAN DEFAULT true,  -- Hauptsystem (falls mehrere)
  notes TEXT,                       -- Interne Notizen
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(location_id, system_id)
);
```

### Vordefinierte Systeme

| Slug | Name | Icon | Notizen |
|------|------|------|---------|
| `thefork` | TheFork | 🍴 | URL-Pattern bekannt |
| `opentable` | OpenTable | 🪑 | URL-Pattern bekannt |
| `resmio` | resmio | 📅 | Deutscher Anbieter |
| `quandoo` | Quandoo | 📱 | |
| `google` | Google Reservierung | 🔍 | Über Google Business |
| `eigen_website` | Eigene Website | 🌐 | Freie URL-Eingabe |
| `eigen_system` | Eigenes System | 💻 | Individuelle Lösung |
| `telefon` | Nur Telefon | 📞 | Telefonnummer erforderlich |
| `whatsapp` | WhatsApp | 💬 | WhatsApp-Nummer erforderlich |
| `email` | Per E-Mail | ✉️ | E-Mail-Adresse erforderlich |
| `keins` | Keine Reservierung möglich | ❌ | Walk-in only |

### Admin-Interface für Betreiber

```
┌─────────────────────────────────────────────────────────────────┐
│  RESERVIERUNGEN VERWALTEN                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Wie können Gäste bei Ihnen reservieren?                       │
│                                                                 │
│  ○ Über ein Online-System                                      │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ System wählen: [TheFork              ▼]                 │ │
│    │ Link zur Reservierungsseite:                            │ │
│    │ [https://www.thefork.de/restaurant/cafe-morgenstern   ] │ │
│    └─────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ○ Per Telefon                                                 │
│    Telefonnummer: [02821-12345        ]                        │
│                                                                 │
│  ○ Per WhatsApp                                                │
│    WhatsApp-Nummer: [+49 171 1234567  ]                        │
│                                                                 │
│  ○ Per E-Mail                                                  │
│    E-Mail: [reservierung@cafe-morgenstern.de]                  │
│                                                                 │
│  ○ Keine Reservierung möglich (nur Walk-in)                    │
│                                                                 │
│  ☑ Reservierung empfohlen (am Wochenende oft voll)            │
│                                                                 │
│  [Speichern]                                                    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  💡 Tipp: Wir bieten auch ein kostenloses Reservierungssystem  │
│     direkt hier im Verzeichnis an. [Mehr erfahren →]           │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend-Darstellung (Lokal-Detailseite)

```
┌─────────────────────────────────────────────────────────────┐
│  RESERVIEREN                                                │
├─────────────────────────────────────────────────────────────┤
│  🍴 Online reservieren bei TheFork                         │
│     [Zur Reservierung →]                                    │
│                                                             │
│  📞 Oder telefonisch: 02821-12345                          │
│     [Jetzt anrufen]                                         │
│                                                             │
│  ⚠️ Reservierung am Wochenende empfohlen                   │
└─────────────────────────────────────────────────────────────┘
```

### Vertriebsnutzen der Daten

Die strukturierte Erfassung ermöglicht:

1. **Marktanalyse:** Welche Systeme werden in der Region genutzt?
2. **Conversion-Tracking:** Wie viele Klicks auf externe Systeme?
3. **Upselling-Potenzial:** Betreiber mit "Nur Telefon" sind Prime-Kandidaten für Option C
4. **Partnerschafts-Möglichkeiten:** Bei hoher TheFork-Nutzung → Affiliate-Gespräche?

**Reporting-Queries:**

```sql
-- Verteilung der Reservierungssysteme
SELECT 
  ers.name,
  COUNT(*) as anzahl,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as prozent
FROM location_external_reservations ler
JOIN external_reservation_systems ers ON ler.system_id = ers.id
GROUP BY ers.name
ORDER BY anzahl DESC;

-- Upselling-Kandidaten (Telefon/WhatsApp/Keins)
SELECT l.name, l.city, ers.name as aktuelles_system
FROM locations l
JOIN location_external_reservations ler ON l.id = ler.location_id
JOIN external_reservation_systems ers ON ler.system_id = ers.id
WHERE ers.slug IN ('telefon', 'whatsapp', 'email', 'keins')
ORDER BY l.city;
```

---

## Option C: Eigenes Reservierungssystem (Flask-Plugin)

### Architektur-Konzept

Das Reservierungssystem wird als **Flask-Plugin/Blueprint** entwickelt, das:

1. In fruehstuecken.click integriert läuft
2. Als eigenständiges Modul in andere Flask-Projekte eingebunden werden kann
3. Für das Cityserver-Franchise wiederverwendbar ist

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRUEHSTUECKEN.CLICK                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Flask App (Hauptanwendung)                               │  │
│  │  ├── /                    → Startseite                    │  │
│  │  ├── /suche               → Verzeichnis-Suche             │  │
│  │  ├── /lokal/<slug>        → Lokal-Detailseite             │  │
│  │  ├── /admin               → Betreiber-Backend             │  │
│  │  │                                                        │  │
│  │  └── /reservierung/       → PLUGIN (Blueprint)            │  │
│  │      ├── /widget/<loc_id> → Einbettbares Widget           │  │
│  │      ├── /buchen          → Buchungs-Flow                 │  │
│  │      ├── /bestaetigung    → Bestätigungsseite             │  │
│  │      ├── /stornieren      → Stornierung                   │  │
│  │      └── /betreiber/      → Betreiber-Dashboard           │  │
│  │          ├── /heute       → Tagesübersicht                │  │
│  │          ├── /kalender    → Wochenansicht                 │  │
│  │          ├── /einstellungen → Kapazitäten etc.            │  │
│  │          └── /api/        → JSON-Endpunkte für PWA        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Plugin-Struktur

```
flask_reservierung/
├── __init__.py              # Blueprint-Definition, init_app()
├── models.py                # SQLAlchemy-Modelle (oder Supabase-Client)
├── routes/
│   ├── __init__.py
│   ├── widget.py            # Gast-Widget Routen
│   ├── booking.py           # Buchungsprozess
│   └── operator.py          # Betreiber-Dashboard
├── services/
│   ├── __init__.py
│   ├── availability.py      # Verfügbarkeits-Logik
│   ├── notifications.py     # SMS/E-Mail-Versand
│   └── validation.py        # Eingabevalidierung
├── templates/
│   ├── widget/
│   │   ├── embed.html       # Einbettbares Widget
│   │   └── standalone.html  # Standalone-Version
│   └── operator/
│       ├── dashboard.html   # Hauptansicht
│       ├── day_view.html    # Tagesübersicht
│       └── settings.html    # Einstellungen
├── static/
│   ├── css/
│   │   └── reservierung.css
│   └── js/
│       ├── widget.js        # Widget-Logik (HTMX-kompatibel)
│       └── operator.js      # Dashboard-Interaktionen
└── config.py                # Plugin-Konfiguration
```

### Blueprint-Registrierung

```python
# flask_reservierung/__init__.py
from flask import Blueprint

reservierung_bp = Blueprint(
    'reservierung',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/reservierung/static',
    url_prefix='/reservierung'
)

def init_app(app, db_client=None, config=None):
    """
    Initialisiert das Reservierungs-Plugin.
    
    Args:
        app: Flask-App-Instanz
        db_client: Supabase-Client oder SQLAlchemy-Session
        config: Plugin-Konfiguration (SMS-Provider, etc.)
    """
    from . import routes
    
    # Konfiguration speichern
    app.config['RESERVIERUNG_DB'] = db_client
    app.config['RESERVIERUNG_CONFIG'] = config or {}
    
    # Blueprint registrieren
    app.register_blueprint(reservierung_bp)
    
    return reservierung_bp


# Verwendung in fruehstuecken.click/app.py
from flask import Flask
from flask_reservierung import init_app as init_reservierung

app = Flask(__name__)
supabase = create_client(...)

init_reservierung(app, db_client=supabase, config={
    'sms_provider': 'twilio',
    'sms_from': '+49...',
    'email_from': 'reservierung@fruehstuecken.click',
    'default_slot_duration': 90,  # Minuten
})
```

### Datenmodell 
```sql
-- ============================================================
-- RESERVIERUNGS-PLUGIN: Datenmodell
-- ============================================================

-- Reservierungen
CREATE TABLE reservations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  location_id UUID NOT NULL,  -- Referenz zur Location (externes FK)
  
  -- Zeitdaten
  reservation_date DATE NOT NULL,
  time_slot TIME NOT NULL,
  duration_minutes INT DEFAULT 90,
  
  -- Gast-Daten
  guest_name TEXT NOT NULL,
  guest_phone TEXT NOT NULL,
  guest_email TEXT,
  party_size INT NOT NULL CHECK (party_size >= 1 AND party_size <= 20),
  
  -- Optionen
  notes TEXT,
  special_requests JSONB DEFAULT '{}',
  -- Beispiel: {"high_chairs": 2, "allergies": "Nüsse", "occasion": "Geburtstag", "terrace": true}
  
  -- Status-Management
  status TEXT DEFAULT 'pending' CHECK (status IN (
    'pending',      -- Neu eingegangen, wartet auf Bestätigung
    'confirmed',    -- Vom Betreiber bestätigt
    'cancelled_guest',    -- Vom Gast storniert
    'cancelled_operator', -- Vom Betreiber storniert
    'completed',    -- Erfolgreich durchgeführt
    'no_show'       -- Gast nicht erschienen
  )),
  
  -- Timestamps
  confirmed_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,
  cancellation_reason TEXT,
  
  -- Tracking
  source TEXT DEFAULT 'widget' CHECK (source IN ('widget', 'phone', 'walkin', 'admin')),
  confirmation_code TEXT UNIQUE,  -- z.B. "FRH-A7X3K"
  
  -- Meta
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Verfügbarkeits-Slots (Kapazitätsplanung)
CREATE TABLE availability_slots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  location_id UUID NOT NULL,
  
  -- Zeitdefinition
  day_of_week INT CHECK (day_of_week BETWEEN 0 AND 6),  -- 0=Sonntag, 6=Samstag
  time_slot TIME NOT NULL,
  
  -- Kapazität
  max_parties INT NOT NULL DEFAULT 5,      -- Max. Anzahl Buchungen pro Slot
  max_guests INT,                           -- Optional: Max. Gesamtpersonen
  
  -- Steuerung
  is_active BOOLEAN DEFAULT true,
  valid_from DATE,                          -- Optional: Gültig ab
  valid_until DATE,                         -- Optional: Gültig bis
  
  -- Meta
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(location_id, day_of_week, time_slot)
);

-- Ausnahmen (Feiertage, Betriebsferien, etc.)
CREATE TABLE availability_exceptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  location_id UUID NOT NULL,
  
  exception_date DATE NOT NULL,
  exception_type TEXT CHECK (exception_type IN ('closed', 'special_hours', 'fully_booked')),
  
  -- Bei 'special_hours': Abweichende Slots
  special_slots JSONB,  -- [{"time": "10:00", "max_parties": 3}, ...]
  
  reason TEXT,  -- z.B. "Betriebsferien", "Weihnachten"
  
  UNIQUE(location_id, exception_date)
);

-- Benachrichtigungs-Log
CREATE TABLE reservation_notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reservation_id UUID REFERENCES reservations(id) ON DELETE CASCADE,
  
  notification_type TEXT CHECK (notification_type IN (
    'confirmation_guest',      -- Bestätigung an Gast
    'confirmation_operator',   -- Neue Buchung an Betreiber
    'reminder_guest',          -- Erinnerung an Gast (z.B. 24h vorher)
    'reminder_operator',       -- Erinnerung an Betreiber
    'cancellation_guest',      -- Stornierung an Gast
    'cancellation_operator'    -- Stornierung an Betreiber
  )),
  channel TEXT CHECK (channel IN ('sms', 'email', 'push')),
  
  sent_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'failed')),
  error_message TEXT
);

-- Plugin-Einstellungen pro Location
CREATE TABLE reservation_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  location_id UUID NOT NULL UNIQUE,
  
  -- Aktivierung
  is_enabled BOOLEAN DEFAULT true,
  
  -- Buchungsregeln
  min_advance_hours INT DEFAULT 2,          -- Min. Vorlauf für Buchung
  max_advance_days INT DEFAULT 30,          -- Max. Tage im Voraus
  default_duration_minutes INT DEFAULT 90,
  max_party_size INT DEFAULT 10,
  
  -- Bestätigungsverhalten
  auto_confirm BOOLEAN DEFAULT false,       -- Automatisch bestätigen?
  require_phone BOOLEAN DEFAULT true,
  require_email BOOLEAN DEFAULT false,
  
  -- Benachrichtigungen
  notify_sms BOOLEAN DEFAULT true,
  notify_email BOOLEAN DEFAULT true,
  reminder_hours_before INT DEFAULT 24,     -- Erinnerung X Stunden vorher
  
  -- Anpassung
  custom_message_confirmation TEXT,         -- Individuelle Bestätigungsnachricht
  custom_message_reminder TEXT,
  
  -- Meta
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indizes für Performance
CREATE INDEX idx_reservations_location_date ON reservations(location_id, reservation_date);
CREATE INDEX idx_reservations_status ON reservations(status);
CREATE INDEX idx_availability_location ON availability_slots(location_id, day_of_week);
```

### Verfügbarkeits-Logik

```python
# flask_reservierung/services/availability.py

from datetime import date, time, datetime, timedelta
from typing import List, Optional

class AvailabilityService:
    def __init__(self, db_client):
        self.db = db_client
    
    def get_available_slots(
        self, 
        location_id: str, 
        target_date: date,
        party_size: int = 2
    ) -> List[dict]:
        """
        Ermittelt verfügbare Zeitslots für ein Datum.
        
        Returns:
            Liste von Slots: [
                {"time": "09:00", "available": True, "remaining": 3},
                {"time": "10:30", "available": False, "remaining": 0},
                ...
            ]
        """
        day_of_week = target_date.weekday()  # 0=Montag in Python
        # Umrechnung auf SQL-Standard (0=Sonntag)
        sql_dow = (day_of_week + 1) % 7
        
        # 1. Prüfen auf Ausnahmen (geschlossen, Sonderöffnung)
        exception = self._get_exception(location_id, target_date)
        if exception and exception['exception_type'] == 'closed':
            return []
        
        # 2. Normale Slots laden
        if exception and exception['exception_type'] == 'special_hours':
            slots = exception['special_slots']
        else:
            slots = self._get_regular_slots(location_id, sql_dow)
        
        # 3. Bestehende Buchungen laden
        bookings = self._get_bookings_for_date(location_id, target_date)
        
        # 4. Verfügbarkeit berechnen
        result = []
        for slot in slots:
            booked_count = sum(
                1 for b in bookings 
                if b['time_slot'] == slot['time_slot'] 
                and b['status'] in ('pending', 'confirmed')
            )
            remaining = slot['max_parties'] - booked_count
            
            result.append({
                'time': slot['time_slot'],
                'available': remaining > 0,
                'remaining': max(0, remaining),
                'max_parties': slot['max_parties']
            })
        
        return result
    
    def is_slot_available(
        self,
        location_id: str,
        target_date: date,
        time_slot: time,
        party_size: int
    ) -> bool:
        """Prüft, ob ein spezifischer Slot buchbar ist."""
        slots = self.get_available_slots(location_id, target_date, party_size)
        for slot in slots:
            if slot['time'] == time_slot.strftime('%H:%M'):
                return slot['available']
        return False
```

---

## Mobile-Lösung für Betreiber

### Entscheidung: PWA vs. Mobile-optimierte Web-Ansicht

| Kriterium | PWA | Mobile Web-Ansicht |
|-----------|-----|-------------------|
| **Installation** | Add to Homescreen | Nur Bookmark |
| **Push-Notifications** | ✅ Ja (mit Service Worker) | ❌ Nein |
| **Offline-Fähigkeit** | ✅ Möglich | ❌ Nein |
| **Entwicklungsaufwand** | Mittel (Service Worker, Manifest) | Niedrig |
| **Update-Prozess** | Automatisch | Automatisch |
| **Native App Feel** | ✅ Ja | ⚠️ Eingeschränkt |

### Empfehlung: Hybrid-Ansatz

**Phase 1: Mobile-optimierte Web-Ansicht (MVP)**
- Responsive Dashboard unter `/reservierung/betreiber/`
- Touch-optimierte UI
- Schnelle Implementierung

**Phase 2: PWA-Upgrade**
- Service Worker hinzufügen
- Web App Manifest
- Push-Notifications
- Offline-Caching der Tagesübersicht

### Mobile Dashboard Design

```
┌─────────────────────────────────────────────────────────────┐
│  ☰  CAFÉ MORGENSTERN        📅 Sa, 11. Jan 2026            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  HEUTE: 8 RESERVIERUNGEN                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│  09:00  ┌──────────────────────────────────────────────┐   │
│         │ 🟡 OFFEN                                      │   │
│         │ Müller, Familie            4 Personen        │   │
│         │ 📞 0171-1234567                               │   │
│         │ 🪑 2 Kinderstühle                             │   │
│         │                                              │   │
│         │ [✓ Bestätigen]  [✗ Ablehnen]  [📞 Anrufen]  │   │
│         └──────────────────────────────────────────────┘   │
│                                                             │
│  09:00  ┌──────────────────────────────────────────────┐   │
│         │ ✅ BESTÄTIGT                                  │   │
│         │ Schmidt, Thomas            2 Personen        │   │
│         │ 📞 0172-9876543                               │   │
│         │ Terrasse gewünscht                           │   │
│         │                                              │   │
│         │ [📞 Anrufen]  [✗ Stornieren]                 │   │
│         └──────────────────────────────────────────────┘   │
│                                                             │
│  10:30  ┌──────────────────────────────────────────────┐   │
│         │ ✅ BESTÄTIGT                                  │   │
│         │ Weber, Anna                6 Personen        │   │
│         │ 📞 0173-5555555                               │   │
│         │ 🎂 Geburtstag!                               │   │
│         └──────────────────────────────────────────────┘   │
│                                                             │
│  ... weitere Buchungen ...                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [  📅 Kalender  ]  [  ➕ Manuell  ]  [  ⚙️ Settings  ]    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### PWA-Konfiguration (Phase 2)

```json
// static/manifest.json
{
  "name": "Reservierungen - fruehstuecken.click",
  "short_name": "Reservierungen",
  "description": "Verwalte deine Frühstücks-Reservierungen",
  "start_url": "/reservierung/betreiber/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#f59e0b",
  "icons": [
    {
      "src": "/static/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

```javascript
// static/js/service-worker.js
const CACHE_NAME = 'reservierung-v1';
const OFFLINE_URL = '/reservierung/betreiber/offline';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        '/reservierung/static/css/operator.css',
        '/reservierung/static/js/operator.js',
        OFFLINE_URL
      ]);
    })
  );
});

self.addEventListener('push', (event) => {
  const data = event.data.json();
  self.registration.showNotification(data.title, {
    body: data.body,
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/badge-72.png',
    data: { url: data.url }
  });
});
```

### Push-Notification-Szenarien

| Ereignis | Notification |
|----------|--------------|
| Neue Reservierung | "🆕 Neue Buchung: Müller, 4 Pers., Sa 09:00" |
| Stornierung durch Gast | "❌ Storniert: Schmidt hat für So 10:30 abgesagt" |
| Erinnerung (1h vorher) | "⏰ In 1h: Weber, 6 Pers. (Geburtstag!)" |
| Kapazitätswarnung | "⚠️ Sa 10:30 fast voll – nur noch 1 Platz" |

---

## Gast-Widget

### Einbettungs-Varianten

**1. Inline-Integration (auf Lokal-Detailseite)**
```html
<!-- In der Lokal-Detailseite -->
<div id="reservierung-widget" 
     hx-get="/reservierung/widget/{{ location.id }}" 
     hx-trigger="load">
  <p>Reservierungsformular wird geladen...</p>
</div>
```

**2. Standalone-Seite**
```
/reservierung/buchen/cafe-morgenstern
```

**3. Embed für externe Websites (iframe)**
```html
<iframe 
  src="https://fruehstuecken.click/reservierung/widget/abc123?embed=true" 
  width="100%" 
  height="400" 
  frameborder="0">
</iframe>
```

### Widget-Flow

```
┌─────────────────────────────────────────────────────────────┐
│  🗓️ TISCH RESERVIEREN                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Wann möchten Sie frühstücken?                             │
│                                                             │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │
│  │ Mo  │ │ Di  │ │ Mi  │ │ Do  │ │ Fr  │ │ Sa  │ │ So  │  │
│  │ 6.  │ │ 7.  │ │ 8.  │ │ 9.  │ │ 10. │ │ 11. │ │ 12. │  │
│  │     │ │     │ │     │ │     │ │  ●  │ │  ●  │ │  ●  │  │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘  │
│                          (nur Sa-So geöffnet)       [▶]    │
│                                                             │
│  Samstag, 11. Januar 2026                                  │
│                                                             │
│  Uhrzeit:                                                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │  09:00  │ │  10:30  │ │  12:00  │ │  13:30  │          │
│  │ 🟢 frei │ │ 🟡 2 fr.│ │ 🔴 voll │ │ 🟢 frei │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│                                                             │
│  Personenzahl:  [ 2 ▼ ]                                    │
│                                                             │
│  [          WEITER          ]                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  📝 IHRE DATEN                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Sa, 11.01. um 09:00 Uhr · 2 Personen                      │
│                                                             │
│  Name *                                                     │
│  [Max Mustermann                    ]                       │
│                                                             │
│  Telefon * (für Rückfragen)                                │
│  [0171-1234567                      ]                       │
│                                                             │
│  E-Mail (optional, für Bestätigung)                        │
│  [max@beispiel.de                   ]                       │
│                                                             │
│  Besondere Wünsche                                         │
│  [ ] Kinderstuhl benötigt  Anzahl: [1]                     │
│  [ ] Terrasse gewünscht (wetterabhängig)                   │
│  [ ] Allergien/Unverträglichkeiten: [____________]         │
│                                                             │
│  Anmerkungen                                               │
│  [                                  ]                       │
│                                                             │
│  [          RESERVIERUNG ABSENDEN          ]                │
│                                                             │
│  Mit dem Absenden akzeptiere ich die Datenschutz-          │
│  bestimmungen und die Stornierungsbedingungen.             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ✅ ANFRAGE GESENDET                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Vielen Dank für Ihre Reservierungsanfrage!                │
│                                                             │
│  Buchungscode: FRH-A7X3K                                   │
│                                                             │
│  📅 Samstag, 11. Januar 2026                               │
│  🕐 09:00 Uhr                                              │
│  👥 2 Personen                                             │
│  📍 Café Morgenstern, Große Straße 15, Kleve               │
│                                                             │
│  ⏳ Das Café wird Ihre Anfrage in Kürze bestätigen.        │
│     Sie erhalten eine SMS an 0171-1234567.                 │
│                                                             │
│  [Zum Kalender hinzufügen]   [Reservierung stornieren]     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Monetarisierung

### Preismodell

| Plan | Monatspreis | Enthält |
|------|-------------|---------|
| **Schnupper** | €0 |  Schnupper Monat mit 5 Reservierungen, E-Mail-Bestätigung, Basis-Dashboard |
| **Starter** | €2,50 | 10 Reservierungen/Monat, E-Mail-Bestätigung, Basis-Dashboard |
| **Standard** | €10 | 150 Reservierungen/Monat, alle Funktionen aus Starter + WhatsApp oder SMS-Benachrichtigungen, Erinnerungen |
| **Premium** | €30 | Unlimitiert Reservierungen, alle Funktionen aus Standard + Push-Notifications, Statistiken, No-Show-Tracking, Prioritäts-Support |

### Upselling-Pfade

```
Option A (Extern)          Option C (Starter)         Option C (Standard/Premium)
      │                           │                            │
      │  "Probieren Sie unser     │   "Upgrade für SMS         │
      │   kostenloses System"     │    und unbegrenzt"         │
      └──────────────────────────►└───────────────────────────►│
                                                               │
                                                       Recurring Revenue
```

### Break-Even-Rechnung (aktualisiert)

**Entwicklungsaufwand:**
- Flask-Plugin MVP: 120h
- Mobile Dashboard: 40h
- PWA-Upgrade (Phase 2): 24h
- **Gesamt Phase 1:** 160h × €80 = €12.800

**Laufende Kosten:**
- SMS (Twilio): ~€0,07/SMS × 500 SMS/Monat = €35
- Supabase: Im bestehenden Plan enthalten
- **Gesamt:** ~€50/Monat

**Einnahmen bei 50 Lokalen:**

| Plan | Anzahl | Preis | Monatlich |
|------|--------|-------|-----------|
| Schnupper | 5 | €0 | €0 |
| Starter | 20 | €2,50 | €50 |
| Standard | 15 | €10 | €150 |
| Premium | 5 | €30 | €150 |
| **Gesamt** | | | **€350** |

**Netto-Einnahmen:** €350 - €50 = €300/Monat
**Break-Even:** €12.800 / €300 = **~43 Monate**

Bei 100 Lokalen mit besserem Plan-Mix (20% Premium):
- Netto-Einnahmen: ~€1.150/Monat
- Break-Even: **~11 Monate**

---

## Implementierungs-Roadmap

### Phase 1: Quick Wins (Woche 1-2)

**Option A Implementierung:**
- [ ] Datenmodell-Migration (externe Systeme)
- [ ] Admin-Interface für System-Auswahl
- [ ] Frontend-Darstellung auf Lokal-Seite
- [ ] Tracking-Events für Klicks auf externe Links

**Deliverables:**
- Betreiber können externes Reservierungssystem verknüpfen
- Erste Daten über Systemverteilung

### Phase 2: Plugin-Grundgerüst (Woche 3-4)

**Option C Basis:**
- [ ] Flask-Blueprint-Struktur
- [ ] Datenmodell (Reservierungen, Slots, Settings)
- [ ] Gast-Widget (Basis-Version)
- [ ] Betreiber-Dashboard (Tagesansicht)
- [ ] E-Mail-Bestätigungen

**Deliverables:**
- Funktionierendes Reservierungssystem (Starter-Plan)
- 3-5 Beta-Tester

### Phase 3: Vollausbau (Woche 5-6)

**Option C Erweiterung:**
- [ ] SMS-Integration (Twilio)
- [ ] Automatische Erinnerungen
- [ ] Kapazitäts-Management UI
- [ ] Stornierungsfunktion
- [ ] Statistiken

**Deliverables:**
- Standard-Plan launchbar
- Mobile Dashboard optimiert

### Phase 4: PWA & Premium (Woche 7-8)

**Mobile & Premium:**
- [ ] PWA Manifest + Service Worker
- [ ] Push-Notifications
- [ ] No-Show-Tracking
- [ ] Erweiterte Statistiken
- [ ] Abo-Management / Billing

**Deliverables:**
- Vollständiges Premium-Angebot
- App-like Experience für Betreiber

---

## Technische Entscheidungen (offen)

### Zu klären vor Implementierung

| Frage | Optionen | Empfehlung |
|-------|----------|------------|
| **SMS-Provider** | Twilio, MessageBird, LINK Mobility | Twilio (beste Docs, DE-Nummern) |
| **E-Mail-Provider** | Supabase Edge + Resend, Mailgun | Resend (einfach, günstig) |
| **Bestätigungs-Flow** | Auto-Confirm vs. Manual | Konfigurierbar pro Lokal |
| **Kalendar-Export** | iCal-Datei vs. Google Calendar API | iCal-Datei (einfacher) |
| **Billing** | Stripe, Paddle, manuell | Stripe (Standard) |

---

## Anhang: Aktualisierte Feature-Gap-Priorisierung

Die Reservierungs-Integration sollte von **Nice-to-Have** auf **Should-Have** hochgestuft werden:

```markdown
### 4.2 Should-Have (Mittlere Priorität)

#### ✅ Reservierungs-Integration (NEU)

**Zwei-Säulen-Modell:**

1. Option A: Externe Systemanbindung
   - Strukturierte Erfassung externer Systeme
   - Vertriebsrelevante Datensammlung
   - Aufwand: Niedrig (1-2 Wochen)

2. Option C: Eigenes Flask-Plugin
   - Integriertes Reservierungssystem
   - PWA für Betreiber
   - Monetarisierung: €0-39/Monat
   - Aufwand: Mittel-Hoch (6-8 Wochen)

**Strategischer Wert:** Hoch
- Differenzierungsmerkmal
- Recurring Revenue
- Lock-in für Betreiber
- Cityserver-Franchise-Template
```

---

*Dokument-Version: 2.0*
*Erstellt: Januar 2026*
*Status: Entwurf zur Diskussion*
