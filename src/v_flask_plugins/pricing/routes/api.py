"""API routes for Pricing plugin.

Provides price calculation API for Shop integration.

Usage:
    GET /api/pricing/price/<product_id>/<customer_id>
    GET /api/pricing/price/<product_id>/<customer_id>?quantity=10

Response:
    {
        "success": true,
        "data": {
            "final_price": "15.00",
            "list_price": "20.00",
            "discount_percent": "25.00",
            "is_discounted": true,
            "rule_applied": "Sonderpreis Q1 2025",
            "rule_id": "uuid..."
        }
    }
"""

from flask import Blueprint, jsonify

from v_flask_plugins.pricing.services import pricing_service


pricing_api_bp = Blueprint(
    'pricing_api',
    __name__,
)


@pricing_api_bp.route('/api/pricing/price/<product_id>/<customer_id>')
def get_price(product_id: str, customer_id: str):
    """Get price for product and customer.

    Args:
        product_id: PIM product UUID
        customer_id: CRM customer UUID

    Returns:
        JSON with price details:
        - final_price: Calculated price for customer
        - list_price: Original list price from PIM
        - discount_percent: Savings in percent
        - is_discounted: Whether price differs from list price
        - rule_applied: Name of applied rule (null if list price)
        - rule_id: ID of applied rule (null if list price)
    """
    try:
        result = pricing_service.prices.get_price(product_id, customer_id)

        return jsonify({
            'success': True,
            'data': {
                'final_price': str(result.final_price),
                'list_price': str(result.list_price),
                'discount_percent': str(result.discount_percent),
                'is_discounted': result.is_discounted,
                'rule_applied': result.rule_applied,
                'rule_id': result.rule_id,
            }
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Interner Fehler',
        }), 500
