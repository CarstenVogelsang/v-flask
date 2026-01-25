"""JWT utilities for API authentication.

Provides stateless authentication for REST APIs using JSON Web Tokens.
Tokens are signed with the Flask app's SECRET_KEY.

Token Payload Structure:
    {
        'user_id': str,      # User identifier (UUID string recommended)
        'user_type': str,    # Type identifier (e.g., 'admin', 'customer', 'user')
        'iat': datetime,     # Issued at timestamp (auto-added)
        'exp': datetime,     # Expiration timestamp (auto-added)
        ... additional custom fields
    }

Usage:
    # Login endpoint - generate token
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        # ... validate credentials ...
        token = generate_token({
            'user_id': str(user.id),
            'user_type': 'customer',
            'email': user.email,
        })
        return {'token': token}

    # Protected endpoint - require token
    @app.route('/api/protected')
    @jwt_required
    def protected():
        user = get_current_api_user()
        return {'message': f'Hello {user["user_id"]}'}
"""

from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any

import jwt
from flask import current_app, g, jsonify, request


# JWT Configuration Defaults
DEFAULT_EXPIRES_HOURS = 24
ALGORITHM = 'HS256'


def generate_token(payload: dict[str, Any], expires_hours: int = DEFAULT_EXPIRES_HOURS) -> str:
    """Generate a JWT token.

    Args:
        payload: Data to encode. Should include at minimum:
            - user_id: Unique user identifier (str)
            - user_type: Type of user ('admin', 'customer', etc.)
        expires_hours: Token validity in hours (default: 24)

    Returns:
        Encoded JWT string

    Raises:
        ValueError: If SECRET_KEY is not configured

    Example:
        >>> token = generate_token({
        ...     'user_id': '550e8400-e29b-41d4-a716-446655440000',
        ...     'user_type': 'customer',
        ...     'customer_number': 'K-2024-00001',
        ... })
    """
    secret = current_app.config.get('SECRET_KEY')
    if not secret:
        raise ValueError("SECRET_KEY must be configured for JWT generation")

    now = datetime.now(timezone.utc)
    token_payload = {
        **payload,
        'iat': now,
        'exp': now + timedelta(hours=expires_hours),
    }

    return jwt.encode(token_payload, secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string to decode

    Returns:
        Decoded payload dictionary or None if:
            - Token is expired
            - Token signature is invalid
            - Token is malformed

    Example:
        >>> payload = decode_token(token_string)
        >>> if payload:
        ...     print(f"User: {payload['user_id']}")
    """
    secret = current_app.config.get('SECRET_KEY')
    if not secret:
        return None

    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        current_app.logger.debug("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        current_app.logger.debug(f"JWT token invalid: {e}")
        return None


def jwt_required(f):
    """Decorator to require valid JWT token for API endpoints.

    Token must be provided in the Authorization header:
        Authorization: Bearer <token>

    On success, the decoded payload is stored in g.jwt_payload
    and can be accessed via get_current_api_user().

    On failure, returns JSON error response with status 401.

    Example:
        @app.route('/api/customers/<customer_id>')
        @jwt_required
        def get_customer(customer_id: str):
            user = get_current_api_user()
            if user['user_type'] == 'customer' and user['user_id'] != customer_id:
                return jsonify({'error': 'forbidden'}), 403
            # ... return customer data ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header:
            return jsonify({
                'error': 'missing_token',
                'message': 'Authorization header required',
            }), 401

        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'invalid_header',
                'message': 'Authorization header must be: Bearer <token>',
            }), 401

        token = auth_header[7:]  # Remove 'Bearer '

        if not token:
            return jsonify({
                'error': 'missing_token',
                'message': 'Token not provided',
            }), 401

        payload = decode_token(token)

        if payload is None:
            return jsonify({
                'error': 'invalid_token',
                'message': 'Token invalid or expired',
            }), 401

        # Store payload in Flask's g object for access in the view
        g.jwt_payload = payload

        return f(*args, **kwargs)

    return decorated


def get_current_api_user() -> dict[str, Any] | None:
    """Get the current API user from JWT payload.

    Must be called within a request context where @jwt_required
    decorator has validated the token.

    Returns:
        Dict containing JWT payload (user_id, user_type, etc.)
        or None if not in a JWT-authenticated context

    Example:
        @app.route('/api/me')
        @jwt_required
        def get_me():
            user = get_current_api_user()
            return {
                'user_id': user['user_id'],
                'user_type': user['user_type'],
            }
    """
    return getattr(g, 'jwt_payload', None)


def optional_jwt(f):
    """Decorator for endpoints that optionally accept JWT.

    If a valid token is provided, the payload is available via
    get_current_api_user(). If no token or invalid token, the
    endpoint proceeds without authentication.

    Useful for endpoints that work differently for authenticated
    vs. anonymous users.

    Example:
        @app.route('/api/products')
        @optional_jwt
        def list_products():
            user = get_current_api_user()
            if user and user['user_type'] == 'customer':
                # Return customer-specific pricing
                pass
            else:
                # Return public pricing
                pass
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            payload = decode_token(token)
            if payload:
                g.jwt_payload = payload

        return f(*args, **kwargs)

    return decorated
