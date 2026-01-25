"""PIM Services - Business logic layer.

Provides centralized access to all PIM services through the pim_service singleton.

Usage:
    from v_flask_plugins.pim.services import pim_service

    # Products
    products = pim_service.search_products('drill')
    product = pim_service.get_product_by_sku('ART-001')

    # Categories
    tree = pim_service.get_category_tree()

    # Barcode validation
    result = pim_service.validate_barcode('4006381333931')
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from slugify import slugify

from v_flask import db

from v_flask_plugins.pim.models import (
    Category,
    TaxRate,
    Product,
    ProductImage,
    Manufacturer,
    Brand,
    Series,
    ProductGroup,
    PriceTag,
)


@dataclass
class BarcodeResult:
    """Result of barcode validation."""

    original: str
    normalized: Optional[str] = None
    type: Optional[str] = None
    is_valid: bool = False
    error: Optional[str] = None


class BarcodeService:
    """Automatic barcode detection and validation.

    Supports GTIN-8, GTIN-12 (UPC-A), GTIN-13 (EAN-13), and GTIN-14.
    """

    TYPE_MAP = {
        8: 'GTIN-8',
        12: 'GTIN-12',  # UPC-A
        13: 'GTIN-13',  # EAN-13
        14: 'GTIN-14',
    }

    def detect_and_validate(self, barcode: str) -> BarcodeResult:
        """Detect barcode type and validate checksum.

        Args:
            barcode: The barcode string to validate.

        Returns:
            BarcodeResult with validation status and type.
        """
        if not barcode:
            return BarcodeResult(
                original='',
                is_valid=False,
                error='Barcode ist leer',
            )

        # Keep only digits
        digits = ''.join(c for c in barcode if c.isdigit())

        if not digits:
            return BarcodeResult(
                original=barcode,
                is_valid=False,
                error='Barcode enthält keine Ziffern',
            )

        # Detect type by length
        barcode_type = self.TYPE_MAP.get(len(digits))
        if not barcode_type:
            return BarcodeResult(
                original=barcode,
                is_valid=False,
                error=f'Ungültige Länge: {len(digits)} Ziffern (erwartet: 8, 12, 13 oder 14)',
            )

        # Validate checksum (Modulo 10)
        if not self._validate_check_digit(digits):
            return BarcodeResult(
                original=barcode,
                type=barcode_type,
                is_valid=False,
                error='Ungültige Prüfziffer',
            )

        return BarcodeResult(
            original=barcode,
            normalized=digits,
            type=barcode_type,
            is_valid=True,
        )

    def _validate_check_digit(self, digits: str) -> bool:
        """Validate Modulo 10 checksum for GTIN.

        The check digit is calculated by:
        1. Sum digits at odd positions (from right) × 3
        2. Sum digits at even positions (from right) × 1
        3. Check digit = (10 - (sum mod 10)) mod 10
        """
        total = 0
        for i, digit in enumerate(digits[:-1]):
            # Weight alternates between 1 and 3, starting from position 1
            weight = 3 if i % 2 == len(digits) % 2 else 1
            total += int(digit) * weight
        check = (10 - (total % 10)) % 10
        return check == int(digits[-1])

    def calculate_check_digit(self, digits: str) -> str:
        """Calculate and append check digit to a barcode without one.

        Args:
            digits: Barcode digits without check digit (7, 11, 12, or 13 digits).

        Returns:
            Complete barcode with check digit.
        """
        total = 0
        # For calculating check digit, we need to consider the final length
        final_length = len(digits) + 1
        for i, digit in enumerate(digits):
            weight = 3 if i % 2 == final_length % 2 else 1
            total += int(digit) * weight
        check = (10 - (total % 10)) % 10
        return digits + str(check)


class CategoryService:
    """Service for category operations."""

    def get_all(self, active_only: bool = True) -> list[Category]:
        """Get all categories."""
        query = Category.query.order_by(Category.sort_order)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    def get_tree(
        self,
        root_id: Optional[str] = None,
        active_only: bool = True,
    ) -> list[dict]:
        """Get hierarchical category tree.

        Args:
            root_id: Optional root category ID. If None, starts from top level.
            active_only: Only include active categories.

        Returns:
            List of category dicts with nested children.
        """
        query = Category.query
        if active_only:
            query = query.filter_by(is_active=True)

        if root_id:
            query = query.filter_by(parent_id=root_id)
        else:
            query = query.filter(Category.parent_id.is_(None))

        query = query.order_by(Category.sort_order)
        categories = query.all()

        return [self._category_to_tree_node(cat, active_only) for cat in categories]

    def _category_to_tree_node(self, category: Category, active_only: bool) -> dict:
        """Convert category to tree node with children."""
        children_query = category.children.order_by(Category.sort_order)
        if active_only:
            children_query = children_query.filter_by(is_active=True)

        return {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'full_path': category.full_path,
            'depth': category.depth,
            'is_active': category.is_active,
            'children': [
                self._category_to_tree_node(child, active_only)
                for child in children_query.all()
            ],
        }

    def get_by_id(self, category_id: str) -> Optional[Category]:
        """Get category by ID."""
        return Category.query.get(category_id)

    def get_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug."""
        return Category.query.filter_by(slug=slug).first()

    def get_breadcrumb(self, category_id: str) -> list[Category]:
        """Get breadcrumb path from root to category."""
        category = self.get_by_id(category_id)
        if not category:
            return []

        path = [category]
        parent = category.parent
        while parent:
            path.insert(0, parent)
            parent = parent.parent
        return path

    def create(
        self,
        name: str,
        slug: Optional[str] = None,
        parent_id: Optional[str] = None,
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> Category:
        """Create a new category."""
        if not slug:
            slug = slugify(name)

        # Ensure unique slug
        base_slug = slug
        counter = 1
        while Category.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1

        category = Category(
            name=name,
            slug=slug,
            parent_id=parent_id,
            description=description,
            is_active=is_active,
        )
        db.session.add(category)
        db.session.commit()
        return category

    def update(self, category_id: str, **kwargs) -> Optional[Category]:
        """Update a category."""
        category = self.get_by_id(category_id)
        if not category:
            return None

        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)

        db.session.commit()
        return category

    def delete(self, category_id: str) -> bool:
        """Delete a category (soft delete by setting is_active=False)."""
        category = self.get_by_id(category_id)
        if not category:
            return False

        category.is_active = False
        db.session.commit()
        return True


class ProductService:
    """Service for product operations."""

    def __init__(self, barcode_service: BarcodeService):
        self.barcode_service = barcode_service

    def get_all(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Product]:
        """Get all products with pagination."""
        query = Product.query.order_by(Product.sort_order, Product.name)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.offset(offset).limit(limit).all()

    def get_count(self, active_only: bool = True) -> int:
        """Get total product count."""
        query = Product.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.count()

    def get_by_id(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        return Product.query.get(product_id)

    def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        return Product.query.filter_by(sku=sku).first()

    def get_by_barcode(self, barcode: str) -> Optional[Product]:
        """Get product by barcode (GTIN/EAN/UPC)."""
        # Normalize the barcode first
        result = self.barcode_service.detect_and_validate(barcode)
        if result.is_valid and result.normalized:
            return Product.query.filter_by(barcode=result.normalized).first()
        # Fallback: try with original barcode
        return Product.query.filter_by(barcode=barcode).first()

    def get_by_category(
        self,
        category_id: str,
        active_only: bool = True,
    ) -> list[Product]:
        """Get all products in a category."""
        query = Product.query.filter_by(category_id=category_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Product.sort_order, Product.name).all()

    def search(
        self,
        query_str: str,
        limit: int = 20,
        category_id: Optional[str] = None,
        active_only: bool = True,
    ) -> list[Product]:
        """Full-text search over name, SKU, and barcode."""
        search_term = f'%{query_str}%'
        query = Product.query.filter(
            db.or_(
                Product.name.ilike(search_term),
                Product.sku.ilike(search_term),
                Product.barcode.ilike(search_term),
                Product.description_short.ilike(search_term),
            )
        )

        if active_only:
            query = query.filter_by(is_active=True)

        if category_id:
            query = query.filter_by(category_id=category_id)

        return query.order_by(Product.name).limit(limit).all()

    def get_featured(self, limit: int = 10) -> list[Product]:
        """Get featured products."""
        return (
            Product.query.filter_by(is_featured=True, is_active=True)
            .order_by(Product.sort_order)
            .limit(limit)
            .all()
        )

    def get_low_stock(self, limit: int = 50) -> list[Product]:
        """Get products with stock below minimum."""
        return (
            Product.query.filter(
                Product.is_active == True,  # noqa: E712
                Product.stock_quantity <= Product.min_stock,
            )
            .order_by(Product.stock_quantity)
            .limit(limit)
            .all()
        )

    def create(
        self,
        name: str,
        sku: str,
        price_net: Decimal,
        **kwargs,
    ) -> Product:
        """Create a new product."""
        # Validate barcode if provided
        barcode = kwargs.get('barcode')
        if barcode:
            result = self.barcode_service.detect_and_validate(barcode)
            if result.is_valid:
                kwargs['barcode'] = result.normalized
                kwargs['barcode_type'] = result.type

        # Calculate gross price if tax rate is provided
        tax_rate_id = kwargs.get('tax_rate_id')
        if tax_rate_id and 'price_gross' not in kwargs:
            tax_rate = TaxRate.query.get(tax_rate_id)
            if tax_rate:
                kwargs['price_gross'] = price_net * (1 + tax_rate.rate / 100)
            else:
                kwargs['price_gross'] = price_net
        elif 'price_gross' not in kwargs:
            kwargs['price_gross'] = price_net

        product = Product(
            name=name,
            sku=sku,
            price_net=price_net,
            **kwargs,
        )
        db.session.add(product)
        db.session.commit()
        return product

    def update(self, product_id: str, **kwargs) -> Optional[Product]:
        """Update a product."""
        product = self.get_by_id(product_id)
        if not product:
            return None

        # Validate barcode if being updated
        if 'barcode' in kwargs and kwargs['barcode']:
            result = self.barcode_service.detect_and_validate(kwargs['barcode'])
            if result.is_valid:
                kwargs['barcode'] = result.normalized
                kwargs['barcode_type'] = result.type

        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)

        db.session.commit()
        return product

    def delete(self, product_id: str) -> bool:
        """Delete a product (soft delete by setting is_active=False)."""
        product = self.get_by_id(product_id)
        if not product:
            return False

        product.is_active = False
        db.session.commit()
        return True


class TaxRateService:
    """Service for tax rate operations."""

    def get_all(self, active_only: bool = True) -> list[TaxRate]:
        """Get all tax rates."""
        query = TaxRate.query.order_by(TaxRate.rate)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    def get_by_id(self, tax_rate_id: str) -> Optional[TaxRate]:
        """Get tax rate by ID."""
        return TaxRate.query.get(tax_rate_id)

    def get_default(self) -> Optional[TaxRate]:
        """Get the default tax rate."""
        return TaxRate.get_default()

    def create(
        self,
        name: str,
        rate: Decimal,
        is_default: bool = False,
    ) -> TaxRate:
        """Create a new tax rate."""
        # If setting as default, unset any existing default
        if is_default:
            TaxRate.query.filter_by(is_default=True).update({'is_default': False})

        tax_rate = TaxRate(
            name=name,
            rate=rate,
            is_default=is_default,
        )
        db.session.add(tax_rate)
        db.session.commit()
        return tax_rate

    def update(self, tax_rate_id: str, **kwargs) -> Optional[TaxRate]:
        """Update a tax rate."""
        tax_rate = self.get_by_id(tax_rate_id)
        if not tax_rate:
            return None

        # If setting as default, unset any existing default
        if kwargs.get('is_default'):
            TaxRate.query.filter(
                TaxRate.id != tax_rate_id,
                TaxRate.is_default == True,  # noqa: E712
            ).update({'is_default': False})

        for key, value in kwargs.items():
            if hasattr(tax_rate, key):
                setattr(tax_rate, key, value)

        db.session.commit()
        return tax_rate

    def delete(self, tax_rate_id: str) -> bool:
        """Delete a tax rate (soft delete)."""
        tax_rate = self.get_by_id(tax_rate_id)
        if not tax_rate:
            return False

        tax_rate.is_active = False
        db.session.commit()
        return True


class ManufacturerService:
    """Service for manufacturer, brand, and series operations."""

    # --- Manufacturers ---

    def get_all_manufacturers(self, active_only: bool = True) -> list[Manufacturer]:
        """Get all manufacturers."""
        query = Manufacturer.query.order_by(Manufacturer.sort_order, Manufacturer.name)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    def get_manufacturer_by_id(self, manufacturer_id: str) -> Optional[Manufacturer]:
        """Get manufacturer by ID."""
        return Manufacturer.query.get(manufacturer_id)

    def create_manufacturer(
        self,
        name: str,
        slug: Optional[str] = None,
        **kwargs,
    ) -> Manufacturer:
        """Create a new manufacturer."""
        if not slug:
            slug = slugify(name)

        # Ensure unique slug
        base_slug = slug
        counter = 1
        while Manufacturer.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1

        manufacturer = Manufacturer(name=name, slug=slug, **kwargs)
        db.session.add(manufacturer)
        db.session.commit()
        return manufacturer

    def update_manufacturer(
        self, manufacturer_id: str, **kwargs
    ) -> Optional[Manufacturer]:
        """Update a manufacturer."""
        manufacturer = self.get_manufacturer_by_id(manufacturer_id)
        if not manufacturer:
            return None

        for key, value in kwargs.items():
            if hasattr(manufacturer, key):
                setattr(manufacturer, key, value)

        db.session.commit()
        return manufacturer

    def delete_manufacturer(self, manufacturer_id: str) -> bool:
        """Delete a manufacturer (soft delete)."""
        manufacturer = self.get_manufacturer_by_id(manufacturer_id)
        if not manufacturer:
            return False

        manufacturer.is_active = False
        db.session.commit()
        return True

    # --- Brands ---

    def get_all_brands(self, active_only: bool = True) -> list[Brand]:
        """Get all brands."""
        query = Brand.query.order_by(Brand.sort_order, Brand.name)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    def get_brands_by_manufacturer(
        self, manufacturer_id: str, active_only: bool = True
    ) -> list[Brand]:
        """Get all brands for a manufacturer."""
        query = Brand.query.filter_by(manufacturer_id=manufacturer_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Brand.sort_order, Brand.name).all()

    def get_brand_by_id(self, brand_id: str) -> Optional[Brand]:
        """Get brand by ID."""
        return Brand.query.get(brand_id)

    def create_brand(
        self,
        name: str,
        manufacturer_id: str,
        slug: Optional[str] = None,
        **kwargs,
    ) -> Brand:
        """Create a new brand."""
        if not slug:
            slug = slugify(name)

        # Ensure unique slug
        base_slug = slug
        counter = 1
        while Brand.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1

        brand = Brand(name=name, manufacturer_id=manufacturer_id, slug=slug, **kwargs)
        db.session.add(brand)
        db.session.commit()
        return brand

    def update_brand(self, brand_id: str, **kwargs) -> Optional[Brand]:
        """Update a brand."""
        brand = self.get_brand_by_id(brand_id)
        if not brand:
            return None

        for key, value in kwargs.items():
            if hasattr(brand, key):
                setattr(brand, key, value)

        db.session.commit()
        return brand

    def delete_brand(self, brand_id: str) -> bool:
        """Delete a brand (soft delete)."""
        brand = self.get_brand_by_id(brand_id)
        if not brand:
            return False

        brand.is_active = False
        db.session.commit()
        return True

    # --- Series ---

    def get_all_series(self, active_only: bool = True) -> list[Series]:
        """Get all series."""
        query = Series.query.order_by(Series.sort_order, Series.name)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    def get_series_by_brand(
        self, brand_id: str, active_only: bool = True
    ) -> list[Series]:
        """Get all series for a brand."""
        query = Series.query.filter_by(brand_id=brand_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Series.sort_order, Series.name).all()

    def get_series_by_id(self, series_id: str) -> Optional[Series]:
        """Get series by ID."""
        return Series.query.get(series_id)

    def create_series(
        self,
        name: str,
        brand_id: str,
        slug: Optional[str] = None,
        **kwargs,
    ) -> Series:
        """Create a new series."""
        if not slug:
            slug = slugify(name)

        # Ensure unique slug
        base_slug = slug
        counter = 1
        while Series.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1

        series = Series(name=name, brand_id=brand_id, slug=slug, **kwargs)
        db.session.add(series)
        db.session.commit()
        return series

    def update_series(self, series_id: str, **kwargs) -> Optional[Series]:
        """Update a series."""
        series = self.get_series_by_id(series_id)
        if not series:
            return None

        for key, value in kwargs.items():
            if hasattr(series, key):
                setattr(series, key, value)

        db.session.commit()
        return series

    def delete_series(self, series_id: str) -> bool:
        """Delete a series (soft delete)."""
        series = self.get_series_by_id(series_id)
        if not series:
            return False

        series.is_active = False
        db.session.commit()
        return True


class ProductGroupService:
    """Service for product group operations."""

    def get_all(self, active_only: bool = True) -> list[ProductGroup]:
        """Get all product groups."""
        query = ProductGroup.query.order_by(ProductGroup.sort_order, ProductGroup.name)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    def get_by_id(self, group_id: str) -> Optional[ProductGroup]:
        """Get product group by ID."""
        return ProductGroup.query.get(group_id)

    def create(
        self,
        name: str,
        slug: Optional[str] = None,
        **kwargs,
    ) -> ProductGroup:
        """Create a new product group."""
        if not slug:
            slug = slugify(name)

        # Ensure unique slug
        base_slug = slug
        counter = 1
        while ProductGroup.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1

        group = ProductGroup(name=name, slug=slug, **kwargs)
        db.session.add(group)
        db.session.commit()
        return group

    def update(self, group_id: str, **kwargs) -> Optional[ProductGroup]:
        """Update a product group."""
        group = self.get_by_id(group_id)
        if not group:
            return None

        for key, value in kwargs.items():
            if hasattr(group, key):
                setattr(group, key, value)

        db.session.commit()
        return group

    def delete(self, group_id: str) -> bool:
        """Delete a product group (soft delete)."""
        group = self.get_by_id(group_id)
        if not group:
            return False

        group.is_active = False
        db.session.commit()
        return True


class PriceTagService:
    """Service for price tag operations."""

    def get_all(self, active_only: bool = True) -> list[PriceTag]:
        """Get all price tags."""
        query = PriceTag.query.order_by(PriceTag.sort_order, PriceTag.name)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    def get_by_id(self, tag_id: str) -> Optional[PriceTag]:
        """Get price tag by ID."""
        return PriceTag.query.get(tag_id)

    def create(
        self,
        name: str,
        slug: Optional[str] = None,
        color: Optional[str] = None,
        **kwargs,
    ) -> PriceTag:
        """Create a new price tag."""
        if not slug:
            slug = slugify(name)

        # Ensure unique slug
        base_slug = slug
        counter = 1
        while PriceTag.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1

        tag = PriceTag(name=name, slug=slug, color=color, **kwargs)
        db.session.add(tag)
        db.session.commit()
        return tag

    def update(self, tag_id: str, **kwargs) -> Optional[PriceTag]:
        """Update a price tag."""
        tag = self.get_by_id(tag_id)
        if not tag:
            return None

        for key, value in kwargs.items():
            if hasattr(tag, key):
                setattr(tag, key, value)

        db.session.commit()
        return tag

    def delete(self, tag_id: str) -> bool:
        """Delete a price tag (soft delete)."""
        tag = self.get_by_id(tag_id)
        if not tag:
            return False

        tag.is_active = False
        db.session.commit()
        return True

    def add_to_product(self, product_id: str, tag_id: str) -> bool:
        """Add a price tag to a product."""
        product = Product.query.get(product_id)
        tag = self.get_by_id(tag_id)
        if not product or not tag:
            return False

        if tag not in product.price_tags.all():
            product.price_tags.append(tag)
            db.session.commit()
        return True

    def remove_from_product(self, product_id: str, tag_id: str) -> bool:
        """Remove a price tag from a product."""
        product = Product.query.get(product_id)
        tag = self.get_by_id(tag_id)
        if not product or not tag:
            return False

        if tag in product.price_tags.all():
            product.price_tags.remove(tag)
            db.session.commit()
        return True


class PIMService:
    """Facade service that provides access to all PIM operations.

    This is the main entry point for all PIM functionality.
    """

    def __init__(self):
        self.barcode = BarcodeService()
        self.categories = CategoryService()
        self.products = ProductService(self.barcode)
        self.tax_rates = TaxRateService()
        self.manufacturers = ManufacturerService()
        self.product_groups = ProductGroupService()
        self.price_tags = PriceTagService()

    # --- Convenience methods for common operations ---

    def get_product_count(self, active_only: bool = True) -> int:
        """Get total product count."""
        return self.products.get_count(active_only)

    def get_category_tree(self, active_only: bool = True) -> list[dict]:
        """Get hierarchical category tree."""
        return self.categories.get_tree(active_only=active_only)

    def search_products(self, query: str, limit: int = 20) -> list[Product]:
        """Search products by name, SKU, or barcode."""
        return self.products.search(query, limit=limit)

    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        return self.products.get_by_sku(sku)

    def get_product_by_barcode(self, barcode: str) -> Optional[Product]:
        """Get product by barcode."""
        return self.products.get_by_barcode(barcode)

    def validate_barcode(self, barcode: str) -> BarcodeResult:
        """Validate a barcode (GTIN/EAN/UPC)."""
        return self.barcode.detect_and_validate(barcode)


# Singleton instance
pim_service = PIMService()

# Exports
__all__ = [
    'pim_service',
    'PIMService',
    'BarcodeService',
    'BarcodeResult',
    'CategoryService',
    'ProductService',
    'TaxRateService',
    'ManufacturerService',
    'ProductGroupService',
    'PriceTagService',
]
