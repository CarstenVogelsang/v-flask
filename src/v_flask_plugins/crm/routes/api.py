"""API routes for CRM plugin.

Provides REST API for shop integration:
- POST /api/crm/auth/login - Shop customer login (returns JWT token)
- GET /api/crm/customers/<id> - Get customer data (requires JWT auth)
- GET /api/crm/customers/<id>/addresses - Get customer addresses (requires JWT auth)

Authentication:
    All endpoints except login require a valid JWT token in the
    Authorization header: Bearer <token>

    Customers can only access their own data (user_type: 'customer').
    Admin users (user_type: 'admin') can access all customer data.
"""

from flask import Blueprint, request, jsonify

from v_flask.api import generate_token, jwt_required, get_current_api_user
from v_flask_plugins.crm.services import crm_service

# API Blueprint
crm_api_bp = Blueprint(
    'crm_api',
    __name__,
    url_prefix='/api/crm'
)


def _check_customer_access(customer_id: str) -> tuple[dict, int] | None:
    """Check if current user has access to the given customer.

    Args:
        customer_id: The customer ID to check access for

    Returns:
        None if access is allowed, or (error_response, status_code) if denied
    """
    user = get_current_api_user()

    # Admins have full access
    if user.get('user_type') == 'admin':
        return None

    # Customers can only access their own data
    if user.get('user_type') == 'customer':
        if user.get('user_id') != customer_id:
            return {
                'error': 'forbidden',
                'message': 'Zugriff verweigert',
            }, 403

    return None


@crm_api_bp.route('/auth/login', methods=['POST'])
def login():
    """Authenticate customer for shop login.

    Request body:
        {
            "email": "customer@example.com",
            "password": "secret123"
        }

    Response (success):
        {
            "success": true,
            "token": "eyJhbGciOiJIUzI1NiIs...",
            "customer": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "customer_number": "K-2025-00001",
                "company_name": "Acme GmbH",
                "email": "customer@example.com"
            }
        }

    Response (error):
        {
            "success": false,
            "error": "invalid_credentials" | "account_locked" | "access_disabled"
        }
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'error': 'invalid_request',
            'message': 'JSON body required'
        }), 400

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({
            'success': False,
            'error': 'invalid_request',
            'message': 'Email and password required'
        }), 400

    result = crm_service.auth.authenticate(email, password)

    if result.success:
        # Generate JWT token with customer info
        token = generate_token({
            'user_id': str(result.customer.id),  # UUID as string
            'user_type': 'customer',
            'customer_number': result.customer.customer_number,
            'email': result.customer.email,
        })

        return jsonify({
            'success': True,
            'token': token,
            'customer': {
                'id': str(result.customer.id),
                'customer_number': result.customer.customer_number,
                'company_name': result.customer.company_name,
                'email': result.customer.email,
            }
        })
    else:
        # Map error codes to HTTP status codes
        status_code = 401
        message_map = {
            'invalid_credentials': 'E-Mail oder Passwort falsch',
            'account_locked': 'Account ist gesperrt. Bitte später erneut versuchen.',
            'access_disabled': 'Shop-Zugang ist deaktiviert',
        }

        return jsonify({
            'success': False,
            'error': result.error,
            'message': message_map.get(result.error, 'Authentifizierung fehlgeschlagen')
        }), status_code


@crm_api_bp.route('/customers/<customer_id>', methods=['GET'])
@jwt_required
def get_customer(customer_id: str):
    """Get customer data by ID.

    Requires JWT authentication. Customers can only access their own data.

    Headers:
        Authorization: Bearer <token>

    Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "customer_number": "K-2025-00001",
            "company_name": "Acme GmbH",
            "email": "customer@example.com",
            "phone": "+49 123 456789",
            "addresses": [...]
        }
    """
    # Check authorization
    access_denied = _check_customer_access(customer_id)
    if access_denied:
        return jsonify(access_denied[0]), access_denied[1]

    customer = crm_service.customers.get_by_id(customer_id)

    if not customer:
        return jsonify({
            'error': 'not_found',
            'message': 'Kunde nicht gefunden'
        }), 404

    # Get addresses
    addresses = crm_service.addresses.get_by_customer(customer_id)

    return jsonify({
        'id': str(customer.id),
        'customer_number': customer.customer_number,
        'company_name': customer.company_name,
        'legal_form': customer.legal_form,
        'email': customer.email,
        'phone': customer.phone,
        'website': customer.website,
        'status': customer.status,
        'addresses': [addr.to_dict() for addr in addresses],
    })


@crm_api_bp.route('/customers/<customer_id>/addresses', methods=['GET'])
@jwt_required
def get_customer_addresses(customer_id: str):
    """Get all addresses for a customer.

    Requires JWT authentication. Customers can only access their own data.

    Headers:
        Authorization: Bearer <token>

    Response:
        {
            "addresses": [
                {
                    "id": "...",
                    "street": "Musterstraße 1",
                    "zip_code": "12345",
                    "city": "Berlin",
                    "country": "DE",
                    "is_default_billing": true,
                    "is_default_shipping": false
                }
            ]
        }
    """
    # Check authorization
    access_denied = _check_customer_access(customer_id)
    if access_denied:
        return jsonify(access_denied[0]), access_denied[1]

    customer = crm_service.customers.get_by_id(customer_id)

    if not customer:
        return jsonify({
            'error': 'not_found',
            'message': 'Kunde nicht gefunden'
        }), 404

    addresses = crm_service.addresses.get_by_customer(customer_id)

    return jsonify({
        'addresses': [addr.to_dict() for addr in addresses],
    })


@crm_api_bp.route('/me', methods=['GET'])
@jwt_required
def get_current_customer():
    """Get current authenticated customer's data.

    Convenience endpoint that uses the customer ID from the JWT token.

    Headers:
        Authorization: Bearer <token>

    Response:
        Same as GET /customers/<id>
    """
    user = get_current_api_user()

    if user.get('user_type') != 'customer':
        return jsonify({
            'error': 'invalid_user_type',
            'message': 'This endpoint is only for customer users'
        }), 403

    customer_id = user.get('user_id')
    customer = crm_service.customers.get_by_id(customer_id)

    if not customer:
        return jsonify({
            'error': 'not_found',
            'message': 'Kunde nicht gefunden'
        }), 404

    addresses = crm_service.addresses.get_by_customer(customer_id)

    return jsonify({
        'id': str(customer.id),
        'customer_number': customer.customer_number,
        'company_name': customer.company_name,
        'legal_form': customer.legal_form,
        'email': customer.email,
        'phone': customer.phone,
        'website': customer.website,
        'status': customer.status,
        'addresses': [addr.to_dict() for addr in addresses],
    })
