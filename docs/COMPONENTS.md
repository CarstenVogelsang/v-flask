# V-Flask UI Components

Wiederverwendbare Jinja2 Macros und JavaScript-Komponenten für Admin-Oberflächen.

## Übersicht

| Komponente | Macro-Datei | Beschreibung |
|------------|-------------|--------------|
| [Icon Picker](#icon-picker) | `icon_picker.html` | Tabler Icon Auswahl mit Drawer |
| [Markdown Editor](#markdown-editor) | `markdown_editor.html` | Textarea mit Markdown-Vorschau |
| [Admin Tile](#admin-tile) | `admin_tile.html` | Dashboard-Kacheln |
| [Admin Group](#admin-group) | `admin_group.html` | Gruppierung von Tiles |
| [Module Header](#module-header) | `module_header.html` | Konsistente Modul-Überschriften |
| [Breadcrumb](#breadcrumb) | `breadcrumb.html` | Navigation-Breadcrumbs |
| [Help](#help) | `help.html` | Hilfe-Tooltips und -Texte |

---

## Icon Picker

Visueller Tabler Icon Picker mit Suchfunktion.

### Dateien

- **Macro:** `v_flask/macros/icon_picker.html`
- **JavaScript:** `v_flask/static/js/icon-picker.js`
- **Icon-Liste:** `v_flask/static/js/tabler-icons-list.json`

### Verwendung

```jinja2
{% from "v_flask/macros/icon_picker.html" import icon_input, icon_picker_drawer %}

{# Im Formular #}
<div class="form-control mb-4">
    {{ icon_input('icon', item.icon, label='Icon', required=true) }}
</div>

{# Einmal pro Seite (am Ende, vor endblock) #}
{{ icon_picker_drawer() }}
```

```jinja2
{# JavaScript einbinden #}
{% block scripts %}
<script src="{{ url_for('v_flask_static.static', filename='js/icon-picker.js') }}"></script>
{% endblock %}
```

### Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `name` | str | - | Feldname (required) |
| `value` | str | `''` | Aktueller Icon-Wert |
| `id` | str | `name` | HTML ID |
| `placeholder` | str | `'ti-icons'` | Placeholder-Icon |
| `label` | str | `None` | Optionales Label |
| `strip_prefix` | bool | `False` | `ti-` Prefix entfernen beim Speichern |
| `required` | bool | `False` | Pflichtfeld |

### CSS für Icon-Grid

Falls das Grid nicht korrekt dargestellt wird:

```css
#iconGrid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
    gap: 4px;
}
```

---

## Markdown Editor

Textarea mit Drag & Drop Bild-Upload und Markdown-Unterstützung.

### Dateien

- **Macro:** `v_flask/macros/markdown_editor.html`
- **JavaScript:** `v_flask/static/js/markdown-editor.js`

### Verwendung

```jinja2
{% from "v_flask/macros/markdown_editor.html" import markdown_editor, markdown_editor_assets %}

{# Im Formular #}
{{ markdown_editor('beschreibung', item.beschreibung, rows=8,
                   placeholder='Markdown wird unterstützt...') }}

{# Assets einmal pro Seite #}
{% block scripts %}
{{ markdown_editor_assets() }}
{% endblock %}
```

### Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `name` | str | - | Feldname (required) |
| `value` | str | `''` | Aktueller Inhalt |
| `rows` | int | `8` | Textarea-Höhe |
| `placeholder` | str | `''` | Placeholder-Text |
| `id` | str | `name` | HTML ID |
| `required` | bool | `False` | Pflichtfeld |
| `upload_url` | str | `/api/upload/image` | Bild-Upload Endpoint |

### Voraussetzungen

- Upload-Endpoint unter `/api/upload/image`
- CSRF-Token verfügbar

---

## Admin Tile

Dashboard-Kacheln für Admin-Übersichtsseiten.

### Dateien

- **Macro:** `v_flask/macros/admin_tile.html`

### Verwendung

```jinja2
{% from "v_flask/macros/admin_tile.html" import admin_tile, admin_tile_grid %}

{% call admin_tile_grid() %}
    {{ admin_tile('Benutzer', 'Benutzerverwaltung', 'ti-users',
                  url_for('admin.users'), color_hex='#3b82f6') }}
    {{ admin_tile('Einstellungen', 'Systemkonfiguration', 'ti-settings',
                  url_for('admin.settings'), color_hex='#10b981',
                  settings_url=url_for('admin.config')) }}
{% endcall %}
```

### Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `name` | str | - | Titel der Kachel |
| `description` | str | - | Beschreibungstext |
| `icon` | str | - | Tabler Icon (mit `ti-` Prefix) |
| `url` | str | - | Ziel-URL |
| `color_hex` | str | `#3b82f6` | Akzentfarbe |
| `settings_url` | str | `None` | Optional: Einstellungs-Button |
| `badge` | int | `None` | Optional: Badge mit Zähler |

---

## Admin Group

Gruppiert Admin-Tiles mit Überschrift.

### Verwendung

```jinja2
{% from "v_flask/macros/admin_group.html" import admin_group %}

{% call admin_group('Inhalte', icon='ti-file-text') %}
    {{ admin_tile(...) }}
    {{ admin_tile(...) }}
{% endcall %}
```

---

## Module Header

Konsistente Modul-Überschriften mit optionalen Aktions-Buttons.

### Verwendung

```jinja2
{% from "v_flask/macros/module_header.html" import module_header %}

{{ module_header('Benutzerverwaltung', icon='ti-users',
                 actions=[
                     {'label': 'Neu', 'url': url_for('admin.user_create'), 'icon': 'ti-plus'}
                 ]) }}
```

---

## Best Practices

1. **Macros importieren:** Immer am Anfang des Templates nach `{% extends %}`
2. **JavaScript/CSS:** Nur einmal pro Seite einbinden (im `scripts` Block)
3. **Drawer/Modals:** Am Ende des Content-Blocks platzieren
4. **Konsistenz:** Gleiche Farben und Icons für gleiche Konzepte verwenden
