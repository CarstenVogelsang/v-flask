"""Catalog service for Shop plugin.

Wrapper around PIM and Pricing services to provide
product data with customer-specific prices.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class ProductWithPrice:
    """Product enriched with customer-specific price data."""

    product: 'Product'
    final_price: Decimal
    list_price: Decimal
    is_discounted: bool
    discount_percent: Decimal


class CatalogService:
    """Service for catalog operations (PIM + Pricing wrapper)."""

    def get_category_tree(self, active_only: bool = True) -> list[dict]:
        """Get hierarchical category tree.

        Args:
            active_only: Only include active categories

        Returns:
            List of category dicts with children
        """
        from v_flask_plugins.pim.services import pim_service

        return pim_service.categories.get_tree(active_only=active_only)

    def get_all_categories(self, active_only: bool = True) -> list['Category']:
        """Get flat list of all categories.

        Args:
            active_only: Only include active categories

        Returns:
            List of Category instances
        """
        from v_flask_plugins.pim.services import pim_service

        return pim_service.categories.get_all(active_only=active_only)

    def get_category_by_id(self, category_id: str) -> Optional['Category']:
        """Get category by ID.

        Args:
            category_id: Category UUID

        Returns:
            Category instance or None
        """
        from v_flask_plugins.pim.services import pim_service

        return pim_service.categories.get_by_id(category_id)

    def get_category_by_slug(self, slug: str) -> Optional['Category']:
        """Get category by slug.

        Args:
            slug: Category URL slug

        Returns:
            Category instance or None
        """
        from v_flask_plugins.pim.services import pim_service

        return pim_service.categories.get_by_slug(slug)

    def get_products_by_category(
        self,
        category_id: str,
        customer_id: str,
        active_only: bool = True,
    ) -> list[ProductWithPrice]:
        """Get products in category with customer prices.

        Args:
            category_id: Category UUID
            customer_id: CRM customer UUID for price lookup
            active_only: Only include active products

        Returns:
            List of ProductWithPrice objects
        """
        from v_flask_plugins.pim.services import pim_service
        from v_flask_plugins.pricing.services import pricing_service

        products = pim_service.products.get_by_category(
            category_id,
            active_only=active_only
        )

        result = []
        for product in products:
            price_result = pricing_service.prices.get_price(
                str(product.id),
                customer_id
            )
            result.append(ProductWithPrice(
                product=product,
                final_price=price_result.final_price,
                list_price=price_result.list_price,
                is_discounted=price_result.is_discounted,
                discount_percent=price_result.discount_percent,
            ))

        return result

    def get_product_by_id(
        self,
        product_id: str,
        customer_id: str,
    ) -> Optional[ProductWithPrice]:
        """Get single product with customer price.

        Args:
            product_id: PIM product UUID
            customer_id: CRM customer UUID for price lookup

        Returns:
            ProductWithPrice or None if product not found
        """
        from v_flask_plugins.pim.services import pim_service
        from v_flask_plugins.pricing.services import pricing_service

        product = pim_service.products.get_by_id(product_id)
        if not product:
            return None

        price_result = pricing_service.prices.get_price(
            product_id,
            customer_id
        )

        return ProductWithPrice(
            product=product,
            final_price=price_result.final_price,
            list_price=price_result.list_price,
            is_discounted=price_result.is_discounted,
            discount_percent=price_result.discount_percent,
        )

    def search_products(
        self,
        query: str,
        customer_id: str,
        limit: int = 20,
    ) -> list[ProductWithPrice]:
        """Search products with customer prices.

        Args:
            query: Search query string
            customer_id: CRM customer UUID for price lookup
            limit: Maximum number of results

        Returns:
            List of ProductWithPrice objects
        """
        from v_flask_plugins.pim.services import pim_service
        from v_flask_plugins.pricing.services import pricing_service

        products = pim_service.products.search(query, limit=limit)

        result = []
        for product in products:
            price_result = pricing_service.prices.get_price(
                str(product.id),
                customer_id
            )
            result.append(ProductWithPrice(
                product=product,
                final_price=price_result.final_price,
                list_price=price_result.list_price,
                is_discounted=price_result.is_discounted,
                discount_percent=price_result.discount_percent,
            ))

        return result
