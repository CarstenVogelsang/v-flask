# Templates & Theming System

Das v-flask Template-System bietet wiederverwendbare Basis-Templates und Jinja2-Macros für konsistente UIs.

## Überblick

```
src/v_flask/
├── templates/
│   └── v_flask/
│       ├── base.html              # Haupt-Basistemplate
│       ├── base_minimal.html      # Minimales Layout (Login, Embeds)
│       └── macros/
│           ├── breadcrumb.html
│           ├── admin_tile.html
│           ├── admin_group.html
│           ├── module_header.html
│           ├── help.html
│           ├── icon_picker.html
│           └── markdown_editor.html
└── static/
    ├── css/
    │   └── v-flask.css
    ├── js/
    │   ├── toast-init.js
    │   ├── icon-picker.js
    │   ├── markdown-editor.js
    │   └── tabler-icons-list.json
    └── tabler-icons/
        ├── tabler-icons.min.css
        └── fonts/
```

## Verwendung in Host-Apps

### Template-Vererbung (Extends Pattern)

Host-Apps erweitern das v-flask Basistemplate und überschreiben selektiv Blöcke:

```jinja2
{# app/templates/base.html #}
{% extends "v_flask/base.html" %}

{% block navbar_left %}
<ul class="navbar-nav">
    <li class="nav-item">
        <a class="nav-link" href="{{ url_for('main.dashboard') }}">Dashboard</a>
    </li>
</ul>
{% endblock %}

{% block content %}
    {# Page content #}
{% endblock %}
```

### Verfügbare Blöcke in base.html

| Block | Zweck |
|-------|-------|
| `title` | Seitentitel |
| `meta` | Meta-Tags |
| `favicon` | Favicon-Link |
| `head_css` | Basis-CSS (Bootstrap, Icons) |
| `branding_css` | CI-Variablen aus Betreiber |
| `extra_css` | Zusätzliches CSS |
| `body_start` | Vor Navbar |
| `navbar` | Komplette Navbar |
| `navbar_brand` | Logo + Name |
| `navbar_left` | Links Navigation |
| `navbar_right` | Rechts Navigation |
| `user_dropdown` | User-Menü Inhalt |
| `toast_container` | Flash Messages |
| `main` | Main-Container |
| `content` | **Hauptinhalt** |
| `footer` | Footer |
| `footer_content` | Footer Inhalt |
| `modals` | Icon Picker, Help Modals |
| `body_end` | Vor Scripts |
| `scripts_base` | Basis-JS |
| `extra_js` | Zusätzliches JS |

## Macros

### Breadcrumb

```jinja2
{% from "v_flask/macros/breadcrumb.html" import breadcrumb %}

{{ breadcrumb([
    {'label': 'Dashboard', 'url': url_for('main.dashboard'), 'icon': 'ti-home'},
    {'label': 'Kunden', 'url': url_for('kunden.liste')},
    {'label': kunde.name}
]) }}
```

### Admin Tiles

Für Dashboard- und Übersichtsseiten:

```jinja2
{% from "v_flask/macros/admin_tile.html" import admin_tile, admin_tile_grid %}

{% call admin_tile_grid() %}
    {{ admin_tile('Benutzer', 'Benutzerverwaltung', 'ti-users',
                  url_for('admin.benutzer'), color_hex='#3b82f6') }}
    {{ admin_tile('Einstellungen', 'Systemkonfiguration', 'ti-settings',
                  url_for('admin.settings'), color_hex='#10b981',
                  badge=5) }}
{% endcall %}
```

**Parameter admin_tile():**
- `name`: Tile-Titel
- `description`: Beschreibungstext
- `icon`: Tabler Icon (mit ti- Prefix)
- `url`: Ziel-URL
- `color_hex`: Akzentfarbe (default: #3b82f6)
- `settings_url`: Optional - zeigt Settings-Button
- `badge`: Optional - Zähler-Badge

### Admin Group

Gruppiert Tiles in Sektionen:

```jinja2
{% from "v_flask/macros/admin_group.html" import admin_group_header %}

{{ admin_group_header('Stammdaten', 'database', '#3b82f6') }}
{# ... Tiles ... #}

{{ admin_group_header('System', 'settings', '#6b7280') }}
{# ... Tiles ... #}
```

Oder als Container:

```jinja2
{% from "v_flask/macros/admin_group.html" import admin_group %}

{% call admin_group('Stammdaten', 'database', '#3b82f6') %}
    {{ admin_tile(...) }}
{% endcall %}
```

### Module Header

Header mit Gradient-Hintergrund für Modul-Seiten:

```jinja2
{% from "v_flask/macros/module_header.html" import module_header %}

{% call module_header(
    title="Kundenverwaltung",
    icon="ti-users",
    color_hex="#3b82f6",
    description="Kunden anlegen und verwalten",
    back_url=url_for('main.dashboard')
) %}
    <a href="{{ url_for('kunden.neu') }}" class="btn btn-primary">
        <i class="ti ti-plus"></i> Neu
    </a>
{% endcall %}
```

Einfache Variante:

```jinja2
{% from "v_flask/macros/module_header.html" import page_header %}

{{ page_header("Einstellungen", "ti-settings", "App-Konfiguration") }}
```

### Help Icon

Zeigt kontextsensitive Hilfe aus der Datenbank:

```jinja2
{% from "v_flask/macros/help.html" import help_icon with context %}

<div class="card-header">
    Branchen {{ help_icon('kunden.detail.branchen') }}
</div>
```

**Voraussetzungen:**
- Context Processor muss `get_help_text(schluessel)` bereitstellen
- Hilfetext-Model mit: schluessel, titel, inhalt_markdown, aktiv

Einfacher Tooltip ohne Datenbank:

```jinja2
{% from "v_flask/macros/help.html" import info_tooltip %}

Feldname {{ info_tooltip('Diese Information wird zur Berechnung verwendet.') }}
```

### Icon Picker

Offcanvas-Dialog zur Auswahl von Tabler Icons:

```jinja2
{% from "v_flask/macros/icon_picker.html" import icon_input, icon_picker_offcanvas %}

{# Im Formular #}
{{ icon_input('icon', modul.icon, label='Icon', strip_prefix=true) }}

{# Einmal pro Seite im modals Block #}
{% block modals %}
    {{ icon_picker_offcanvas() }}
{% endblock %}

{# JavaScript einbinden #}
{% block extra_js %}
    <script src="{{ url_for('v_flask_static.static', filename='js/icon-picker.js') }}"></script>
{% endblock %}
```

**Parameter icon_input():**
- `name`: Feldname
- `value`: Aktueller Wert
- `id`: HTML ID (default: name)
- `placeholder`: Platzhalter-Icon
- `label`: Optionales Label
- `strip_prefix`: true = speichert ohne ti- Prefix
- `required`: Pflichtfeld

### Markdown Editor

Editor mit Bild-Upload (Drag & Drop, Paste):

```jinja2
{% from "v_flask/macros/markdown_editor.html" import markdown_editor, markdown_editor_assets %}

{# Im Formular #}
{{ markdown_editor('beschreibung', task.beschreibung, rows=8,
                   placeholder='Markdown wird unterstützt...') }}

{# Assets einmal pro Seite #}
{% block extra_js %}
    {{ markdown_editor_assets() }}
{% endblock %}
```

**Parameter:**
- `name`: Feldname
- `value`: Aktueller Inhalt
- `rows`: Textarea-Höhe (default: 8)
- `placeholder`: Platzhaltertext
- `id`: HTML ID (default: name)
- `required`: Pflichtfeld
- `upload_url`: Custom Upload-URL (default: /api/upload/image)

Markdown rendern:

```jinja2
{% from "v_flask/macros/markdown_editor.html" import markdown_display %}

{{ markdown_display(task.beschreibung) }}
```

## CSS Custom Properties

v-flask definiert CSS-Variablen für Theming:

```css
:root {
    --v-primary: #3b82f6;
    --v-secondary: #64748b;
    --v-navbar-bg: var(--v-primary);
    --v-navbar-text: #ffffff;
    --v-footer-bg: #f8fafc;
    --v-footer-text: #64748b;
}
```

Diese werden automatisch durch `Betreiber.get_css_variables()` überschrieben.

## Markdown Filter

Der `|markdown` Jinja-Filter konvertiert Markdown zu HTML:

```jinja2
{{ beschreibung|markdown|safe }}
```

**Voraussetzung:** `pip install markdown` oder `uv add v-flask[markdown]`

Bei fehlendem Package wird Text escaped zurückgegeben.

## Static Files

Static Files werden über den `v_flask_static` Blueprint bereitgestellt:

```jinja2
<link rel="stylesheet" href="{{ url_for('v_flask_static.static', filename='css/v-flask.css') }}">
<script src="{{ url_for('v_flask_static.static', filename='js/icon-picker.js') }}"></script>
```

## Tabler Icons

Über 5.000 Icons verfügbar. Verwendung:

```html
<i class="ti ti-home"></i>
<i class="ti ti-users"></i>
<i class="ti ti-settings"></i>
```

Siehe [Tabler Icons](https://tabler.io/icons) für die vollständige Liste.
