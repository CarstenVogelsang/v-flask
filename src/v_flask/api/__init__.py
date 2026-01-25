"""v-flask API Module.

Provides JWT-based authentication for REST APIs.

This module is optional and requires the 'api' extra:
    pip install v-flask[api]

Usage:
    from v_flask.api import generate_token, jwt_required, get_current_api_user

    # Generate token after authentication
    token = generate_token({
        'user_id': str(user.id),
        'user_type': 'customer',
    })

    # Protect API endpoint
    @app.route('/api/protected')
    @jwt_required
    def protected_endpoint():
        user = get_current_api_user()
        return {'user_id': user['user_id']}
"""

try:
    import jwt as _jwt  # noqa: F401
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


def _check_jwt_available():
    """Check if PyJWT is installed."""
    if not JWT_AVAILABLE:
        raise ImportError(
            "PyJWT is required for API authentication. "
            "Install it with: pip install v-flask[api]"
        )


# Lazy imports to avoid ImportError if PyJWT not installed
def generate_token(*args, **kwargs):
    """Generate a JWT token.

    Args:
        payload: Data to encode (e.g., {'user_id': ..., 'user_type': 'customer'})
        expires_hours: Token validity in hours (default: 24)

    Returns:
        Encoded JWT string
    """
    _check_jwt_available()
    from v_flask.api.jwt import generate_token as _generate_token
    return _generate_token(*args, **kwargs)


def decode_token(*args, **kwargs):
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string

    Returns:
        Decoded payload dict or None if invalid/expired
    """
    _check_jwt_available()
    from v_flask.api.jwt import decode_token as _decode_token
    return _decode_token(*args, **kwargs)


def jwt_required(f):
    """Decorator to require valid JWT token for API endpoints.

    Token should be in Authorization header: Bearer <token>
    Decoded payload available via get_current_api_user().

    Returns:
        401 Unauthorized if token missing or invalid
    """
    _check_jwt_available()
    from v_flask.api.jwt import jwt_required as _jwt_required
    return _jwt_required(f)


def get_current_api_user():
    """Get the current API user from JWT payload.

    Must be called within a @jwt_required decorated endpoint.

    Returns:
        Dict with user_id, user_type, etc. or None if not in JWT context
    """
    _check_jwt_available()
    from v_flask.api.jwt import get_current_api_user as _get_current_api_user
    return _get_current_api_user()


def optional_jwt(f):
    """Decorator for endpoints that optionally accept JWT.

    If a valid token is provided, the payload is available via
    get_current_api_user(). If no token or invalid token, the
    endpoint proceeds without authentication.
    """
    _check_jwt_available()
    from v_flask.api.jwt import optional_jwt as _optional_jwt
    return _optional_jwt(f)


__all__ = [
    'JWT_AVAILABLE',
    'generate_token',
    'decode_token',
    'jwt_required',
    'optional_jwt',
    'get_current_api_user',
]
