"""Pricing Plugin Services.

Provides:
- pricing_service: Facade for all pricing operations
- PriceService: Price calculation
- RuleService: Rule CRUD operations
- PriceResult: Dataclass for price calculation results

Usage:
    from v_flask_plugins.pricing.services import pricing_service

    # Get price for customer
    result = pricing_service.prices.get_price(product_id, customer_id)
    print(f"Final price: {result.final_price}")

    # Manage rules
    rules = pricing_service.rules.get_rules_for_customer(customer_id)
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from v_flask.extensions import db


@dataclass
class PriceResult:
    """Result of price calculation.

    Attributes:
        final_price: Calculated price for customer
        list_price: Original list price from PIM
        discount_percent: Savings in percent (0 if no discount)
        rule_applied: Name of applied rule (None if list price)
        rule_id: ID of applied rule (None if list price)
        is_discounted: True if price differs from list price
    """
    final_price: Decimal
    list_price: Decimal
    discount_percent: Decimal
    rule_applied: Optional[str]
    rule_id: Optional[str]
    is_discounted: bool


class PriceService:
    """Service for price calculation.

    POC Algorithm:
    1. Get list price from PIM
    2. Look for customer_product rule
    3. If found: apply rule (fixed price or percentage discount)
    4. If not found: return list price
    """

    def get_price(
        self,
        product_id: str,
        customer_id: str,
    ) -> PriceResult:
        """Calculate price for product and customer.

        Args:
            product_id: PIM product UUID (string)
            customer_id: CRM customer UUID (string)

        Returns:
            PriceResult with final price and details

        Raises:
            ValueError: If product not found
        """
        from v_flask_plugins.pim.services import pim_service
        from v_flask_plugins.pricing.models import PricingRule, PriceType

        # 1. Get product from PIM
        product = pim_service.products.get_by_id(product_id)
        if not product:
            raise ValueError(f"Produkt {product_id} nicht gefunden")

        list_price = Decimal(str(product.price_net))

        # 2. Look for customer-specific rule
        rule = PricingRule.query.filter_by(
            customer_id=customer_id,
            product_id=product_id,
            is_active=True,
        ).first()

        # 3. No rule found - return list price
        if not rule:
            return PriceResult(
                final_price=list_price,
                list_price=list_price,
                discount_percent=Decimal('0'),
                rule_applied=None,
                rule_id=None,
                is_discounted=False,
            )

        # 4. Apply rule
        if rule.price_type == PriceType.FIXED.value:
            final_price = Decimal(str(rule.price_value))
        else:  # DISCOUNT_PERCENT
            discount = list_price * (Decimal(str(rule.price_value)) / 100)
            final_price = (list_price - discount).quantize(Decimal('0.01'))

        # Calculate savings percent
        if list_price > 0:
            discount_percent = (
                (list_price - final_price) / list_price * 100
            ).quantize(Decimal('0.01'))
        else:
            discount_percent = Decimal('0')

        return PriceResult(
            final_price=final_price,
            list_price=list_price,
            discount_percent=discount_percent,
            rule_applied=rule.name,
            rule_id=str(rule.id),
            is_discounted=final_price != list_price,
        )


class RuleService:
    """Service for pricing rule CRUD operations."""

    def get_by_id(self, rule_id: str) -> Optional['PricingRule']:
        """Get rule by ID.

        Args:
            rule_id: UUID of the rule

        Returns:
            PricingRule or None if not found
        """
        from v_flask_plugins.pricing.models import PricingRule
        return PricingRule.query.get(rule_id)

    def get_rules_for_customer(self, customer_id: str) -> list['PricingRule']:
        """Get all rules for a customer.

        Args:
            customer_id: CRM customer UUID

        Returns:
            List of PricingRule objects, ordered by creation date (newest first)
        """
        from v_flask_plugins.pricing.models import PricingRule
        return PricingRule.query.filter_by(
            customer_id=customer_id
        ).order_by(PricingRule.created_at.desc()).all()

    def get_rule_for_product(
        self,
        customer_id: str,
        product_id: str,
    ) -> Optional['PricingRule']:
        """Get specific rule for customer-product combination.

        Args:
            customer_id: CRM customer UUID
            product_id: PIM product UUID

        Returns:
            PricingRule or None if not found
        """
        from v_flask_plugins.pricing.models import PricingRule
        return PricingRule.query.filter_by(
            customer_id=customer_id,
            product_id=product_id,
        ).first()

    def create(
        self,
        customer_id: str,
        product_id: str,
        name: str,
        price_type: str,
        price_value: Decimal,
        note: Optional[str] = None,
    ) -> 'PricingRule':
        """Create a new pricing rule.

        Args:
            customer_id: CRM customer UUID
            product_id: PIM product UUID
            name: Rule name/description
            price_type: 'fixed' or 'discount_percent'
            price_value: Price in EUR or discount percentage
            note: Optional internal note

        Returns:
            Created PricingRule

        Raises:
            ValueError: If rule already exists or validation fails
        """
        from v_flask_plugins.pricing.models import PricingRule, RuleType

        # Check for existing rule
        existing = self.get_rule_for_product(customer_id, product_id)
        if existing:
            raise ValueError(
                f"Preisregel für dieses Produkt existiert bereits (ID: {existing.id})"
            )

        rule = PricingRule(
            customer_id=customer_id,
            product_id=product_id,
            name=name.strip(),
            rule_type=RuleType.CUSTOMER_PRODUCT.value,
            price_type=price_type,
            price_value=price_value,
            note=note,
            is_active=True,
        )

        db.session.add(rule)
        db.session.commit()

        return rule

    def update(
        self,
        rule_id: str,
        name: Optional[str] = None,
        price_type: Optional[str] = None,
        price_value: Optional[Decimal] = None,
        note: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> 'PricingRule':
        """Update an existing rule.

        Args:
            rule_id: UUID of the rule to update
            name: New rule name (optional)
            price_type: New price type (optional)
            price_value: New price value (optional)
            note: New note (optional)
            is_active: New active status (optional)

        Returns:
            Updated PricingRule

        Raises:
            ValueError: If rule not found
        """
        rule = self.get_by_id(rule_id)
        if not rule:
            raise ValueError("Preisregel nicht gefunden")

        if name is not None:
            rule.name = name.strip()
        if price_type is not None:
            rule.price_type = price_type
        if price_value is not None:
            rule.price_value = price_value
        if note is not None:
            rule.note = note
        if is_active is not None:
            rule.is_active = is_active

        db.session.commit()
        return rule

    def delete(self, rule_id: str) -> bool:
        """Delete a rule.

        Args:
            rule_id: UUID of the rule to delete

        Returns:
            True if deleted, False if not found
        """
        rule = self.get_by_id(rule_id)
        if not rule:
            return False

        db.session.delete(rule)
        db.session.commit()
        return True

    def get_rules_count(self, customer_id: str) -> int:
        """Get count of rules for a customer.

        Args:
            customer_id: CRM customer UUID

        Returns:
            Number of pricing rules
        """
        from v_flask_plugins.pricing.models import PricingRule
        return PricingRule.query.filter_by(customer_id=customer_id).count()


class PricingService:
    """Facade providing access to all pricing operations.

    Usage:
        from v_flask_plugins.pricing.services import pricing_service

        # Price calculation
        result = pricing_service.prices.get_price(product_id, customer_id)

        # Rule management
        rules = pricing_service.rules.get_rules_for_customer(customer_id)
    """

    def __init__(self):
        self._price_service: Optional[PriceService] = None
        self._rule_service: Optional[RuleService] = None

    @property
    def prices(self) -> PriceService:
        """Get price calculation service."""
        if self._price_service is None:
            self._price_service = PriceService()
        return self._price_service

    @property
    def rules(self) -> RuleService:
        """Get rule management service."""
        if self._rule_service is None:
            self._rule_service = RuleService()
        return self._rule_service


# Singleton instance
pricing_service = PricingService()

__all__ = [
    'PriceResult',
    'PriceService',
    'RuleService',
    'PricingService',
    'pricing_service',
]
