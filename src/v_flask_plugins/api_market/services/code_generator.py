"""Code example generator service.

Generates code examples in multiple languages from OpenAPI endpoints.
Supports: Python, C# (.NET), Delphi
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from v_flask_plugins.api_market.models import ExternalApi

SUPPORTED_LANGUAGES = ['python', 'csharp', 'delphi']


def generate_code_example(
    endpoint: dict,
    api: 'ExternalApi',
    language: str,
    api_key_placeholder: str = 'YOUR_API_KEY'
) -> str:
    """Generate a code example for an endpoint.

    Args:
        endpoint: Endpoint dictionary from OpenAPI spec.
        api: ExternalApi model instance.
        language: Target language ('python', 'csharp', 'delphi').
        api_key_placeholder: Placeholder text for API key.

    Returns:
        Code example as string.

    Raises:
        ValueError: If language is not supported.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f'Unsupported language: {language}. Supported: {SUPPORTED_LANGUAGES}')

    generators = {
        'python': _generate_python,
        'csharp': _generate_csharp,
        'delphi': _generate_delphi,
    }

    return generators[language](endpoint, api, api_key_placeholder)


def _generate_python(endpoint: dict, api: 'ExternalApi', api_key: str) -> str:
    """Generate Python code example using requests library."""
    method = endpoint['method']
    path = endpoint['path']
    base_url = api.base_url or 'https://api.example.com'
    auth_header = api.auth_header_name

    # Build query parameters
    query_params = _extract_query_params(endpoint)
    params_code = ''
    if query_params:
        params_dict = ', '.join(f'"{p["name"]}": ""' for p in query_params)
        params_code = f'\n    params={{{params_dict}}},'

    # Build URL
    url = f'{base_url}{path}'

    code = f'''import requests

API_KEY = "{api_key}"
BASE_URL = "{base_url}"

response = requests.{method.lower()}(
    f"{{BASE_URL}}{path}",
    headers={{"{auth_header}": API_KEY}},{params_code}
)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Error: {{response.status_code}}")
    print(response.text)
'''
    return code


def _generate_csharp(endpoint: dict, api: 'ExternalApi', api_key: str) -> str:
    """Generate C# (.NET) code example using HttpClient."""
    method = endpoint['method']
    path = endpoint['path']
    base_url = api.base_url or 'https://api.example.com'
    auth_header = api.auth_header_name

    # Build query string
    query_params = _extract_query_params(endpoint)
    query_string = ''
    if query_params:
        params = '&'.join(f'{p["name"]}=' for p in query_params)
        query_string = f'?{params}'

    url = f'{base_url}{path}{query_string}'

    code = f'''using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;

class Program
{{
    private static readonly HttpClient client = new HttpClient();
    private const string API_KEY = "{api_key}";
    private const string BASE_URL = "{base_url}";

    static async Task Main()
    {{
        client.DefaultRequestHeaders.Add("{auth_header}", API_KEY);

        var response = await client.{_csharp_method(method)}Async(
            "{url}"
        );

        if (response.IsSuccessStatusCode)
        {{
            var json = await response.Content.ReadAsStringAsync();
            var data = JsonSerializer.Deserialize<JsonDocument>(json);
            Console.WriteLine(json);
        }}
        else
        {{
            Console.WriteLine($"Error: {{(int)response.StatusCode}}");
            Console.WriteLine(await response.Content.ReadAsStringAsync());
        }}
    }}
}}
'''
    return code


def _generate_delphi(endpoint: dict, api: 'ExternalApi', api_key: str) -> str:
    """Generate Delphi code example using THTTPClient."""
    method = endpoint['method']
    path = endpoint['path']
    base_url = api.base_url or 'https://api.example.com'
    auth_header = api.auth_header_name

    # Build query string
    query_params = _extract_query_params(endpoint)
    query_string = ''
    if query_params:
        params = '&'.join(f'{p["name"]}=' for p in query_params)
        query_string = f'?{params}'

    url = f'{base_url}{path}{query_string}'
    delphi_method = _delphi_method(method)

    code = f'''program ApiExample;

{{$APPTYPE CONSOLE}}

uses
  System.SysUtils,
  System.Net.HttpClient,
  System.JSON;

const
  API_KEY = '{api_key}';
  BASE_URL = '{base_url}';

var
  Client: THTTPClient;
  Response: IHTTPResponse;
  JSON: TJSONObject;
begin
  Client := THTTPClient.Create;
  try
    Client.CustomHeaders['{auth_header}'] := API_KEY;

    Response := Client.{delphi_method}('{url}');

    if Response.StatusCode = 200 then
    begin
      JSON := TJSONObject.ParseJSONValue(Response.ContentAsString) as TJSONObject;
      try
        WriteLn(JSON.ToString);
      finally
        JSON.Free;
      end;
    end
    else
    begin
      WriteLn('Error: ', Response.StatusCode);
      WriteLn(Response.ContentAsString);
    end;
  finally
    Client.Free;
  end;
end.
'''
    return code


def _extract_query_params(endpoint: dict) -> list[dict]:
    """Extract query parameters from endpoint definition."""
    params = endpoint.get('parameters', [])
    return [p for p in params if p.get('in') == 'query']


def _csharp_method(method: str) -> str:
    """Convert HTTP method to C# HttpClient method name."""
    return method.capitalize()  # Get, Post, Put, Delete


def _delphi_method(method: str) -> str:
    """Convert HTTP method to Delphi THTTPClient method name."""
    methods = {
        'GET': 'Get',
        'POST': 'Post',
        'PUT': 'Put',
        'DELETE': 'Delete',
        'PATCH': 'Patch',
    }
    return methods.get(method, 'Get')


def generate_all_examples(endpoint: dict, api: 'ExternalApi') -> dict[str, str]:
    """Generate code examples in all supported languages.

    Args:
        endpoint: Endpoint dictionary from OpenAPI spec.
        api: ExternalApi model instance.

    Returns:
        Dictionary mapping language to code example.
    """
    return {
        lang: generate_code_example(endpoint, api, lang)
        for lang in SUPPORTED_LANGUAGES
    }
