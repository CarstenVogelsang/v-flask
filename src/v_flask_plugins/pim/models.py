"""Database models for the PIM (Product Information Management) plugin.

All tables use the 'pim_' prefix for namespace isolation.

Hierarchy:
    Manufacturer → Brand → Series → Product
    Category (tree structure)
    ProductGroup (for pricing rules)
    PriceTag (N:M with Product)
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from v_flask import db


# Association table for Product ↔ PriceTag (N:M)
product_price_tags = db.Table(
    'pim_product_price_tag',
    db.Column('product_id', db.String(36), db.ForeignKey('pim_product.id'), primary_key=True),
    db.Column('price_tag_id', db.String(36), db.ForeignKey('pim_price_tag.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow, nullable=False),
)


class Category(db.Model):
    """Hierarchical product category.

    Categories form a tree structure via parent_id.
    Used for product navigation and filtering.
    """

    __tablename__ = 'pim_category'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = db.Column(db.String(36), db.ForeignKey('pim_category.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True)

    # Self-referential relationship for tree structure
    parent = db.relationship(
        'Category',
        remote_side=[id],
        backref=db.backref('children', lazy='dynamic', order_by='Category.sort_order'),
    )

    # Products in this category
    products = db.relationship('Product', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.id}: {self.name}>'

    @property
    def full_path(self) -> str:
        """Return full category path (e.g., 'Electronics > Phones > Smartphones')."""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)

    @property
    def depth(self) -> int:
        """Return depth in tree (0 = root)."""
        depth = 0
        parent = self.parent
        while parent:
            depth += 1
            parent = parent.parent
        return depth


class TaxRate(db.Model):
    """Tax rate configuration.

    Defines VAT/tax rates that can be assigned to products.
    One rate should be marked as default for new products.
    """

    __tablename__ = 'pim_tax_rate'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    rate = db.Column(db.Numeric(5, 2), nullable=False)  # e.g., 19.00 for 19%
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Products using this tax rate
    products = db.relationship('Product', back_populates='tax_rate', lazy='dynamic')

    def __repr__(self):
        return f'<TaxRate {self.name}: {self.rate}%>'

    @classmethod
    def get_default(cls) -> Optional['TaxRate']:
        """Get the default tax rate."""
        return cls.query.filter_by(is_default=True, is_active=True).first()


class Manufacturer(db.Model):
    """Product manufacturer.

    Top level of the product hierarchy: Manufacturer → Brand → Series → Product.
    """

    __tablename__ = 'pim_manufacturer'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), unique=True, nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True)

    # Brands belonging to this manufacturer
    brands = db.relationship(
        'Brand',
        back_populates='manufacturer',
        lazy='dynamic',
        order_by='Brand.sort_order',
    )

    # Direct product relationship
    products = db.relationship('Product', back_populates='manufacturer', lazy='dynamic')

    def __repr__(self):
        return f'<Manufacturer {self.name}>'


class Brand(db.Model):
    """Product brand, belongs to a manufacturer.

    Example: Bosch (Manufacturer) → Bosch Professional (Brand)
    """

    __tablename__ = 'pim_brand'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    manufacturer_id = db.Column(
        db.String(36), db.ForeignKey('pim_manufacturer.id'), nullable=False
    )
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True)

    # Unique constraint: brand name per manufacturer
    __table_args__ = (
        db.UniqueConstraint('manufacturer_id', 'name', name='uq_brand_manufacturer_name'),
    )

    # Relationships
    manufacturer = db.relationship('Manufacturer', back_populates='brands')
    series = db.relationship(
        'Series', back_populates='brand', lazy='dynamic', order_by='Series.sort_order'
    )
    products = db.relationship('Product', back_populates='brand', lazy='dynamic')

    def __repr__(self):
        return f'<Brand {self.name} ({self.manufacturer.name if self.manufacturer else "?"})>'


class Series(db.Model):
    """Product series, belongs to a brand.

    Example: Bosch Professional (Brand) → 18V-System (Series)
    Optional - products can belong directly to a brand without a series.
    """

    __tablename__ = 'pim_series'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id = db.Column(db.String(36), db.ForeignKey('pim_brand.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True)

    # Unique constraint: series name per brand
    __table_args__ = (
        db.UniqueConstraint('brand_id', 'name', name='uq_series_brand_name'),
    )

    # Relationships
    brand = db.relationship('Brand', back_populates='series')
    products = db.relationship('Product', back_populates='series', lazy='dynamic')

    def __repr__(self):
        return f'<Series {self.name} ({self.brand.name if self.brand else "?"})>'


class ProductGroup(db.Model):
    """Product group for pricing rules.

    Used by the Pricing plugin to apply discounts/surcharges to groups of products.
    Example: "Professional Tools" group gets 5% discount for B2B customers.
    """

    __tablename__ = 'pim_product_group'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), unique=True, nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True)

    # Products in this group
    products = db.relationship('Product', back_populates='product_group', lazy='dynamic')

    def __repr__(self):
        return f'<ProductGroup {self.name}>'


class PriceTag(db.Model):
    """Price tag for flexible product labeling.

    Products can have multiple price tags (N:M relationship).
    Used for marketing labels and pricing rule targeting.

    Examples: "New", "Sale", "Discontinued", "Bestseller"
    """

    __tablename__ = 'pim_price_tag'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    color = db.Column(db.String(7), nullable=True)  # Hex color, e.g., '#FF0000'
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True)

    # N:M relationship to products
    products = db.relationship(
        'Product',
        secondary=product_price_tags,
        back_populates='price_tags',
        lazy='dynamic',
    )

    def __repr__(self):
        return f'<PriceTag {self.name}>'


class Product(db.Model):
    """Main product entity.

    Contains all product master data including:
    - Identification (SKU, barcode)
    - Descriptions
    - Pricing (net, gross, cost)
    - Inventory (stock, unit, minimum)
    - Relationships (category, manufacturer, brand, series, group, tags)

    Prepared for V1 variants with is_parent/parent_id fields.
    """

    __tablename__ = 'pim_product'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Identification
    sku = db.Column(db.String(100), unique=True, nullable=False)
    barcode = db.Column(db.String(50), nullable=True)  # GTIN/EAN/UPC
    barcode_type = db.Column(db.String(20), nullable=True)  # 'GTIN-8', 'GTIN-12', 'GTIN-13', 'GTIN-14'

    # Product information
    name = db.Column(db.String(255), nullable=False)
    description_short = db.Column(db.String(500), nullable=True)
    description_long = db.Column(db.Text, nullable=True)

    # Category relationship
    category_id = db.Column(db.String(36), db.ForeignKey('pim_category.id'), nullable=True)

    # Tax rate relationship
    tax_rate_id = db.Column(db.String(36), db.ForeignKey('pim_tax_rate.id'), nullable=True)

    # Pricing
    price_net = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    price_gross = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)  # Purchase price

    # Inventory
    stock_quantity = db.Column(db.Numeric(10, 3), default=Decimal('0'), nullable=False)
    stock_unit = db.Column(db.String(20), default='Stück', nullable=False)
    min_stock = db.Column(db.Numeric(10, 3), default=Decimal('0'), nullable=False)

    # Physical properties
    weight_kg = db.Column(db.Numeric(8, 3), nullable=True)

    # Status flags
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True)

    # --- V1: Variant preparation ---
    is_parent = db.Column(db.Boolean, default=False, nullable=False)
    parent_id = db.Column(db.String(36), db.ForeignKey('pim_product.id'), nullable=True)

    # --- Product hierarchy ---
    manufacturer_id = db.Column(
        db.String(36), db.ForeignKey('pim_manufacturer.id'), nullable=True
    )
    brand_id = db.Column(db.String(36), db.ForeignKey('pim_brand.id'), nullable=True)
    series_id = db.Column(db.String(36), db.ForeignKey('pim_series.id'), nullable=True)
    product_group_id = db.Column(
        db.String(36), db.ForeignKey('pim_product_group.id'), nullable=True
    )

    # Relationships
    category = db.relationship('Category', back_populates='products')
    tax_rate = db.relationship('TaxRate', back_populates='products')
    manufacturer = db.relationship('Manufacturer', back_populates='products')
    brand = db.relationship('Brand', back_populates='products')
    series = db.relationship('Series', back_populates='products')
    product_group = db.relationship('ProductGroup', back_populates='products')
    images = db.relationship(
        'ProductImage',
        back_populates='product',
        lazy='dynamic',
        order_by='ProductImage.sort_order',
        cascade='all, delete-orphan',
    )

    # Self-referential for variants (V1)
    parent = db.relationship(
        'Product',
        remote_side=[id],
        backref=db.backref('variants', lazy='dynamic'),
    )

    # N:M relationship to price tags
    price_tags = db.relationship(
        'PriceTag',
        secondary=product_price_tags,
        back_populates='products',
        lazy='dynamic',
    )

    def __repr__(self):
        return f'<Product {self.sku}: {self.name}>'

    @property
    def main_image(self) -> Optional['ProductImage']:
        """Get the main product image."""
        return self.images.filter_by(is_main=True).first() or self.images.first()

    @property
    def main_image_url(self) -> Optional[str]:
        """Get URL of main product image."""
        img = self.main_image
        return img.file_path if img else None

    @property
    def margin(self) -> Optional[Decimal]:
        """Calculate profit margin if cost price is set."""
        if self.cost_price and self.price_net:
            return self.price_net - self.cost_price
        return None

    @property
    def margin_percent(self) -> Optional[Decimal]:
        """Calculate margin percentage if cost price is set."""
        if self.cost_price and self.price_net and self.price_net > 0:
            return ((self.price_net - self.cost_price) / self.price_net) * 100
        return None

    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below minimum threshold."""
        return self.stock_quantity <= self.min_stock

    def calculate_gross_price(self) -> Decimal:
        """Calculate gross price from net price and tax rate."""
        if self.tax_rate:
            return self.price_net * (1 + self.tax_rate.rate / 100)
        return self.price_net


class ProductImage(db.Model):
    """Product image.

    Products can have multiple images. One image should be marked as main.
    Images can be sorted via sort_order.
    Supports local storage and S3 (via storage_type).
    """

    __tablename__ = 'pim_product_image'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = db.Column(
        db.String(36), db.ForeignKey('pim_product.id'), nullable=False
    )

    # File information
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)  # Bytes
    mime_type = db.Column(db.String(100), nullable=True)

    # Metadata
    alt_text = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_main = db.Column(db.Boolean, default=False, nullable=False)

    # Storage type (for S3 support in V1)
    storage_type = db.Column(db.String(20), default='local', nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    product = db.relationship('Product', back_populates='images')

    def __repr__(self):
        return f'<ProductImage {self.id}: {self.filename}>'

    @property
    def url(self) -> str:
        """Get public URL for the image."""
        if self.storage_type == 'local':
            return f'/static/uploads/pim/{self.file_path}'
        # S3 URL would be returned here in V1
        return self.file_path
