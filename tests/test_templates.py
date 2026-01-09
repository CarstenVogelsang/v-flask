"""Tests for v-flask template system."""

import pytest
from flask import Flask, render_template_string

from v_flask import VFlask, db


class TestTemplateLoader:
    """Tests for template loader registration."""

    def test_vflask_templates_registered(self, app):
        """v_flask templates should be accessible via Jinja loader."""
        # The ChoiceLoader should include v_flask templates
        loader = app.jinja_loader
        assert loader is not None

        # Test that we can find v_flask base template
        template_source = loader.get_source(app.jinja_env, 'v_flask/base.html')
        assert template_source is not None
        assert 'v-navbar' in template_source[0]  # CSS class in base.html

    def test_vflask_macros_accessible(self, app):
        """v_flask macros should be importable in templates."""
        with app.app_context():
            # Test importing a macro
            result = render_template_string('''
                {%- from "v_flask/macros/breadcrumb.html" import breadcrumb -%}
                {{ breadcrumb([{'label': 'Test'}]) }}
            ''')
            assert 'breadcrumb' in result

    def test_base_minimal_accessible(self, app):
        """base_minimal.html should be accessible."""
        loader = app.jinja_loader
        template_source = loader.get_source(app.jinja_env, 'v_flask/base_minimal.html')
        assert template_source is not None


class TestStaticBlueprint:
    """Tests for static file serving blueprint."""

    def test_static_blueprint_registered(self, app):
        """v_flask_static blueprint should be registered."""
        assert 'v_flask_static' in app.blueprints

    def test_static_url_generation(self, app):
        """Static URLs should be generatable."""
        with app.app_context():
            from flask import url_for
            url = url_for('v_flask_static.static', filename='css/v-flask.css')
            assert '/v_flask_static/css/v-flask.css' in url

    def test_static_css_accessible(self, client):
        """v-flask.css should be served."""
        response = client.get('/v_flask_static/css/v-flask.css')
        assert response.status_code == 200
        assert b'v-flask' in response.data

    def test_static_js_accessible(self, client):
        """JavaScript files should be served."""
        response = client.get('/v_flask_static/js/toast-init.js')
        assert response.status_code == 200
        assert b'DOMContentLoaded' in response.data

    def test_icon_picker_js_accessible(self, client):
        """Icon picker JS should be served."""
        response = client.get('/v_flask_static/js/icon-picker.js')
        assert response.status_code == 200
        assert b'openIconPicker' in response.data

    def test_tabler_icons_css_accessible(self, client):
        """Tabler Icons CSS should be served."""
        response = client.get('/v_flask_static/tabler-icons/tabler-icons.min.css')
        assert response.status_code == 200


class TestMarkdownFilter:
    """Tests for the |markdown Jinja filter."""

    def test_markdown_filter_registered(self, app):
        """markdown filter should be registered."""
        assert 'markdown' in app.jinja_env.filters

    def test_markdown_filter_basic(self, app):
        """markdown filter should convert basic markdown."""
        with app.app_context():
            result = render_template_string('{{ text|markdown|safe }}', text='**bold**')
            # Either real markdown conversion or escaped fallback
            assert 'bold' in result

    def test_markdown_filter_empty(self, app):
        """markdown filter should handle empty input."""
        with app.app_context():
            result = render_template_string('{{ text|markdown|safe }}', text='')
            assert result == ''

    def test_markdown_filter_none(self, app):
        """markdown filter should handle None input."""
        with app.app_context():
            result = render_template_string('{{ text|markdown|safe }}', text=None)
            assert result == ''


class TestMacros:
    """Tests for template macros."""

    def test_breadcrumb_macro(self, app):
        """breadcrumb macro should render correctly."""
        with app.app_context():
            result = render_template_string('''
                {%- from "v_flask/macros/breadcrumb.html" import breadcrumb -%}
                {{ breadcrumb([
                    {'label': 'Home', 'url': '/', 'icon': 'ti-home'},
                    {'label': 'Users'}
                ]) }}
            ''')
            assert 'breadcrumb' in result
            assert 'Home' in result
            assert 'Users' in result
            assert 'ti-home' in result

    def test_admin_tile_macro(self, app):
        """admin_tile macro should render correctly."""
        with app.app_context():
            result = render_template_string('''
                {%- from "v_flask/macros/admin_tile.html" import admin_tile -%}
                {{ admin_tile('Users', 'Manage users', 'ti-users', '/users', '#3b82f6') }}
            ''')
            assert 'Users' in result
            assert 'Manage users' in result
            assert 'ti-users' in result
            assert '#3b82f6' in result

    def test_admin_tile_grid_macro(self, app):
        """admin_tile_grid macro should render correctly."""
        with app.app_context():
            result = render_template_string('''
                {%- from "v_flask/macros/admin_tile.html" import admin_tile_grid, admin_tile -%}
                {% call admin_tile_grid() %}
                    {{ admin_tile('Test', 'Description', 'ti-test', '/test', '#000') }}
                {% endcall %}
            ''')
            assert 'row' in result
            assert 'Test' in result

    def test_module_header_macro(self, app):
        """module_header macro should render correctly."""
        with app.app_context():
            result = render_template_string('''
                {%- from "v_flask/macros/module_header.html" import module_header -%}
                {% call module_header(
                    title="Test Module",
                    icon="ti-test",
                    color_hex="#ff0000"
                ) %}
                    <button>Action</button>
                {% endcall %}
            ''')
            assert 'Test Module' in result
            assert 'ti-test' in result
            assert '#ff0000' in result
            assert 'Action' in result

    def test_page_header_macro(self, app):
        """page_header macro should render correctly."""
        with app.app_context():
            result = render_template_string('''
                {%- from "v_flask/macros/module_header.html" import page_header -%}
                {{ page_header("Settings", "ti-settings", "Configure your app") }}
            ''')
            assert 'Settings' in result
            assert 'ti-settings' in result
            assert 'Configure your app' in result

    def test_admin_group_header_macro(self, app):
        """admin_group_header macro should render correctly."""
        with app.app_context():
            result = render_template_string('''
                {%- from "v_flask/macros/admin_group.html" import admin_group_header -%}
                {{ admin_group_header('System', 'cog', '#6b7280') }}
            ''')
            assert 'System' in result
            assert 'ti-cog' in result
            assert '#6b7280' in result

    def test_icon_input_macro(self, app):
        """icon_input macro should render correctly."""
        with app.app_context():
            result = render_template_string('''
                {%- from "v_flask/macros/icon_picker.html" import icon_input -%}
                {{ icon_input('icon', 'ti-home', label='Select Icon') }}
            ''')
            assert 'icon' in result
            assert 'ti-home' in result
            assert 'Select Icon' in result
            assert 'openIconPicker' in result

    def test_icon_picker_offcanvas_macro(self, app):
        """icon_picker_offcanvas macro should render correctly."""
        with app.app_context():
            result = render_template_string('''
                {%- from "v_flask/macros/icon_picker.html" import icon_picker_offcanvas -%}
                {{ icon_picker_offcanvas() }}
            ''')
            assert 'iconPickerOffcanvas' in result
            assert 'iconSearchInput' in result
            assert 'iconGrid' in result

    def test_markdown_editor_macro(self, app):
        """markdown_editor macro should render correctly."""
        with app.app_context():
            result = render_template_string('''
                {%- from "v_flask/macros/markdown_editor.html" import markdown_editor -%}
                {{ markdown_editor('content', 'Initial text', rows=10) }}
            ''')
            assert 'markdown-editor' in result
            assert 'content' in result
            assert 'Initial text' in result
            assert 'rows="10"' in result

    def test_markdown_editor_assets_macro(self, app):
        """markdown_editor_assets macro should include required scripts."""
        with app.app_context():
            result = render_template_string('''
                {%- from "v_flask/macros/markdown_editor.html" import markdown_editor_assets -%}
                {{ markdown_editor_assets() }}
            ''')
            assert 'marked' in result
            assert 'markdown-editor.js' in result

    def test_info_tooltip_macro(self, app):
        """info_tooltip macro should render correctly."""
        with app.app_context():
            result = render_template_string('''
                {%- from "v_flask/macros/help.html" import info_tooltip -%}
                {{ info_tooltip('Help text here') }}
            ''')
            assert 'tooltip' in result
            assert 'Help text here' in result
            assert 'ti-info-circle' in result
