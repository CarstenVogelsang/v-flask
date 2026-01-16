"""Documentation generator service.

Generates HTML documentation from OpenAPI specs.
"""

from typing import TYPE_CHECKING
from markupsafe import Markup, escape

if TYPE_CHECKING:
    from v_flask_plugins.api_market.models import ExternalApi


def generate_quickstart(spec: dict, api: 'ExternalApi') -> str:
    """Generate quickstart documentation HTML.

    Args:
        spec: Parsed OpenAPI spec.
        api: ExternalApi model instance.

    Returns:
        HTML string with quickstart documentation.
    """
    info = spec.get('info', {})
    title = info.get('title', api.name)
    description = info.get('description', api.description or '')
    version = info.get('version', '')
    base_url = api.base_url or ''

    # Find a simple GET endpoint for the example
    example_endpoint = _find_example_endpoint(spec)
    example_code = ''
    if example_endpoint:
        from v_flask_plugins.api_market.services.code_generator import generate_code_example
        example_code = generate_code_example(example_endpoint, api, 'python')

    html = f'''
<div class="quickstart-docs">
    <h1>{escape(title)}</h1>
    {f'<span class="badge badge-outline">v{escape(version)}</span>' if version else ''}

    <div class="description mt-4">
        {_markdown_to_html(description)}
    </div>

    <h2 class="mt-6">Authentifizierung</h2>
    <p>Alle API-Anfragen erfordern einen API-Key im <code>{escape(api.auth_header_name)}</code> Header:</p>
    <pre><code>{escape(api.auth_header_name)}: YOUR_API_KEY</code></pre>

    <h2 class="mt-6">Basis-URL</h2>
    <pre><code>{escape(base_url)}</code></pre>

    {f"""
    <h2 class="mt-6">Schnellstart-Beispiel</h2>
    <p>Einfaches Beispiel für den Einstieg:</p>
    <pre><code class="language-python">{escape(example_code)}</code></pre>
    """ if example_code else ''}
</div>
'''
    return html


def generate_endpoint_docs(spec: dict) -> str:
    """Generate endpoint documentation HTML.

    Args:
        spec: Parsed OpenAPI spec.

    Returns:
        HTML string with endpoint documentation.
    """
    from v_flask_plugins.api_market.services.openapi_fetcher import extract_endpoints

    endpoints = extract_endpoints(spec)
    if not endpoints:
        return '<p class="text-gray-500">Keine Endpoints gefunden.</p>'

    # Group by tags
    grouped = {}
    for endpoint in endpoints:
        tags = endpoint.get('tags', ['Sonstige'])
        tag = tags[0] if tags else 'Sonstige'
        if tag not in grouped:
            grouped[tag] = []
        grouped[tag].append(endpoint)

    html_parts = ['<div class="endpoint-docs">']

    for tag, tag_endpoints in grouped.items():
        html_parts.append(f'<h2 class="mt-6">{escape(tag)}</h2>')
        html_parts.append('<div class="endpoints-list">')

        for ep in tag_endpoints:
            method_class = _get_method_class(ep['method'])
            html_parts.append(f'''
            <div class="endpoint-item card bg-base-100 shadow-sm mb-4">
                <div class="card-body">
                    <div class="flex items-center gap-2">
                        <span class="badge {method_class}">{ep['method']}</span>
                        <code class="text-sm">{escape(ep['path'])}</code>
                    </div>
                    {f'<p class="mt-2">{escape(ep["summary"])}</p>' if ep['summary'] else ''}
                    {_generate_parameters_table(ep['parameters']) if ep['parameters'] else ''}
                </div>
            </div>
            ''')

        html_parts.append('</div>')

    html_parts.append('</div>')
    return '\n'.join(html_parts)


def _find_example_endpoint(spec: dict) -> dict | None:
    """Find a simple GET endpoint to use as example."""
    from v_flask_plugins.api_market.services.openapi_fetcher import extract_endpoints

    endpoints = extract_endpoints(spec)
    # Prefer GET endpoints with fewer required parameters
    get_endpoints = [e for e in endpoints if e['method'] == 'GET']

    if not get_endpoints:
        return endpoints[0] if endpoints else None

    # Sort by number of required parameters
    def param_count(ep):
        return len([p for p in ep.get('parameters', []) if p.get('required', False)])

    get_endpoints.sort(key=param_count)
    return get_endpoints[0]


def _get_method_class(method: str) -> str:
    """Get CSS class for HTTP method badge."""
    classes = {
        'GET': 'badge-success',
        'POST': 'badge-primary',
        'PUT': 'badge-warning',
        'PATCH': 'badge-warning',
        'DELETE': 'badge-error',
    }
    return classes.get(method, 'badge-ghost')


def _generate_parameters_table(parameters: list[dict]) -> str:
    """Generate HTML table for endpoint parameters."""
    if not parameters:
        return ''

    rows = []
    for param in parameters:
        name = param.get('name', '')
        in_loc = param.get('in', '')
        required = 'Ja' if param.get('required', False) else 'Nein'
        description = param.get('description', '')
        schema = param.get('schema', {})
        param_type = schema.get('type', '')

        rows.append(f'''
        <tr>
            <td><code>{escape(name)}</code></td>
            <td>{escape(in_loc)}</td>
            <td>{escape(param_type)}</td>
            <td>{required}</td>
            <td>{escape(description)}</td>
        </tr>
        ''')

    return f'''
    <div class="overflow-x-auto mt-4">
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>Parameter</th>
                    <th>In</th>
                    <th>Typ</th>
                    <th>Required</th>
                    <th>Beschreibung</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    '''


def _markdown_to_html(text: str) -> str:
    """Convert simple markdown to HTML.

    Handles basic formatting without external dependencies.
    """
    if not text:
        return ''

    # Escape HTML first
    text = str(escape(text))

    # Convert markdown-like formatting
    import re

    # Code blocks
    text = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code>\2</code></pre>', text, flags=re.DOTALL)

    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)

    # Italic
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)

    # Line breaks
    text = text.replace('\n\n', '</p><p>')
    text = text.replace('\n', '<br>')

    return Markup(f'<p>{text}</p>')
