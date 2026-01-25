# PIM Plugin - Technische Architektur

## Schichtenmodell

```
┌─────────────────────────────────────────────────────────┐
│                    Admin UI (NiceGUI)                   │
│  Produkte | Kategorien | Bilder | Steuersätze | Import  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      API Layer                          │
│            /api/pim/products, /api/pim/categories       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                        │
│  ProductService | CategoryService | ImageService | ...  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Repository Layer                      │
│      ProductRepository | CategoryRepository | ...       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      Database                           │
│              PostgreSQL / Firebird (Legacy)             │
└─────────────────────────────────────────────────────────┘
```

---

## Datenmodell

### MVP-Tabellen

```
┌─────────────────────────────────────────────────────────┐
│                     pim_category                        │
├─────────────────────────────────────────────────────────┤
│ id              UUID PRIMARY KEY                        │
│ parent_id       UUID FK → pim_category (nullable)       │
│ name            VARCHAR(255) NOT NULL                   │
│ slug            VARCHAR(255) UNIQUE NOT NULL            │
│ description     TEXT                                    │
│ image_path      VARCHAR(500)                            │
│ sort_order      INTEGER DEFAULT 0                       │
│ is_active       BOOLEAN DEFAULT TRUE                    │
│ created_at      TIMESTAMP DEFAULT NOW()                 │
│ updated_at      TIMESTAMP                               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                     pim_tax_rate                        │
├─────────────────────────────────────────────────────────┤
│ id              UUID PRIMARY KEY                        │
│ name            VARCHAR(100) NOT NULL                   │
│ rate            DECIMAL(5,2) NOT NULL  -- z.B. 19.00    │
│ is_default      BOOLEAN DEFAULT FALSE                   │
│ is_active       BOOLEAN DEFAULT TRUE                    │
│ created_at      TIMESTAMP DEFAULT NOW()                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                     pim_product                         │
├─────────────────────────────────────────────────────────┤
│ id              UUID PRIMARY KEY                        │
│ sku             VARCHAR(100) UNIQUE NOT NULL            │
│ barcode         VARCHAR(50)  -- GTIN/EAN/UPC            │
│ barcode_type    VARCHAR(20)  -- 'GTIN', 'EAN13', 'UPC'  │
│ name            VARCHAR(255) NOT NULL                   │
│ description_short  VARCHAR(500)                         │
│ description_long   TEXT                                 │
│ category_id     UUID FK → pim_category                  │
│ tax_rate_id     UUID FK → pim_tax_rate                  │
│ price_net       DECIMAL(10,2) NOT NULL                  │
│ price_gross     DECIMAL(10,2) NOT NULL                  │
│ cost_price      DECIMAL(10,2)  -- Einkaufspreis         │
│ stock_quantity  DECIMAL(10,3) DEFAULT 0                 │
│ stock_unit      VARCHAR(20) DEFAULT 'Stück'             │
│ min_stock       DECIMAL(10,3) DEFAULT 0                 │
│ weight_kg       DECIMAL(8,3)                            │
│ is_active       BOOLEAN DEFAULT TRUE                    │
│ is_featured     BOOLEAN DEFAULT FALSE                   │
│ sort_order      INTEGER DEFAULT 0                       │
│ created_at      TIMESTAMP DEFAULT NOW()                 │
│ updated_at      TIMESTAMP                               │
│ ----------- V1: Varianten-Vorbereitung -----------      │
│ is_parent       BOOLEAN DEFAULT FALSE                   │
│ parent_id       UUID FK → pim_product (nullable)        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   pim_product_image                     │
├─────────────────────────────────────────────────────────┤
│ id              UUID PRIMARY KEY                        │
│ product_id      UUID FK → pim_product NOT NULL          │
│ filename        VARCHAR(255) NOT NULL                   │
│ original_name   VARCHAR(255)                            │
│ file_path       VARCHAR(500) NOT NULL                   │
│ file_size       INTEGER                                 │
│ mime_type       VARCHAR(100)                            │
│ alt_text        VARCHAR(255)                            │
│ sort_order      INTEGER DEFAULT 0                       │
│ is_main         BOOLEAN DEFAULT FALSE                   │
│ storage_type    VARCHAR(20) DEFAULT 'local'             │
│ created_at      TIMESTAMP DEFAULT NOW()                 │
└─────────────────────────────────────────────────────────┘
```

### V1-Tabellen (Varianten)

```
┌─────────────────────────────────────────────────────────┐
│                  pim_variant_attribute                  │
├─────────────────────────────────────────────────────────┤
│ id              UUID PRIMARY KEY                        │
│ name            VARCHAR(100) NOT NULL  -- 'Größe'       │
│ code            VARCHAR(50) UNIQUE NOT NULL -- 'size'   │
│ type            VARCHAR(20) DEFAULT 'select'            │
│ sort_order      INTEGER DEFAULT 0                       │
│ is_active       BOOLEAN DEFAULT TRUE                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│               pim_variant_attribute_value               │
├─────────────────────────────────────────────────────────┤
│ id              UUID PRIMARY KEY                        │
│ attribute_id    UUID FK → pim_variant_attribute         │
│ value           VARCHAR(100) NOT NULL  -- 'XL'          │
│ code            VARCHAR(50) NOT NULL   -- 'xl'          │
│ sort_order      INTEGER DEFAULT 0                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              pim_product_variant_value                  │
├─────────────────────────────────────────────────────────┤
│ product_id      UUID FK → pim_product                   │
│ attribute_value_id  UUID FK → pim_variant_attr_value    │
│ PRIMARY KEY (product_id, attribute_value_id)            │
└─────────────────────────────────────────────────────────┘
```

### V1-Tabellen (Mehrsprachigkeit)

```
┌─────────────────────────────────────────────────────────┐
│                     pim_language                        │
├─────────────────────────────────────────────────────────┤
│ id              UUID PRIMARY KEY                        │
│ code            VARCHAR(5) UNIQUE NOT NULL  -- 'de'     │
│ name            VARCHAR(50) NOT NULL        -- 'Deutsch'│
│ is_default      BOOLEAN DEFAULT FALSE                   │
│ is_active       BOOLEAN DEFAULT TRUE                    │
│ sort_order      INTEGER DEFAULT 0                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                pim_product_translation                  │
├─────────────────────────────────────────────────────────┤
│ id              UUID PRIMARY KEY                        │
│ product_id      UUID FK → pim_product NOT NULL          │
│ language_id     UUID FK → pim_language NOT NULL         │
│ name            VARCHAR(255)                            │
│ description_short  VARCHAR(500)                         │
│ description_long   TEXT                                 │
│ UNIQUE (product_id, language_id)                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│               pim_category_translation                  │
├─────────────────────────────────────────────────────────┤
│ id              UUID PRIMARY KEY                        │
│ category_id     UUID FK → pim_category NOT NULL         │
│ language_id     UUID FK → pim_language NOT NULL         │
│ name            VARCHAR(255)                            │
│ description     TEXT                                    │
│ UNIQUE (category_id, language_id)                       │
└─────────────────────────────────────────────────────────┘
```

---

## Barcode-Handling

### Unterstützte Formate

| Format | Länge | Prüfziffer | Beispiel |
|--------|-------|------------|----------|
| GTIN-8 | 8 | Ja (Mod 10) | 12345670 |
| GTIN-12 (UPC-A) | 12 | Ja (Mod 10) | 012345678905 |
| GTIN-13 (EAN-13) | 13 | Ja (Mod 10) | 4006381333931 |
| GTIN-14 | 14 | Ja (Mod 10) | 14006381333938 |

### Intelligentes Handling

```python
class BarcodeService:
    """Automatische Barcode-Erkennung und Validierung"""
    
    def detect_and_validate(self, barcode: str) -> BarcodeResult:
        """
        Erkennt Barcode-Typ automatisch und validiert.
        
        Returns:
            BarcodeResult(
                original="4006381333931",
                normalized="4006381333931",  # Führende Nullen ergänzt
                type="GTIN-13",
                is_valid=True,
                error=None
            )
        """
        # Nur Ziffern behalten
        digits = ''.join(c for c in barcode if c.isdigit())
        
        # Typ anhand Länge erkennen
        type_map = {
            8: "GTIN-8",
            12: "GTIN-12",  # UPC-A
            13: "GTIN-13",  # EAN-13
            14: "GTIN-14"
        }
        
        barcode_type = type_map.get(len(digits))
        if not barcode_type:
            return BarcodeResult(
                original=barcode,
                is_valid=False,
                error=f"Ungültige Länge: {len(digits)} Ziffern"
            )
        
        # Prüfziffer validieren (Modulo 10)
        if not self._validate_check_digit(digits):
            return BarcodeResult(
                original=barcode,
                type=barcode_type,
                is_valid=False,
                error="Ungültige Prüfziffer"
            )
        
        return BarcodeResult(
            original=barcode,
            normalized=digits,
            type=barcode_type,
            is_valid=True
        )
    
    def _validate_check_digit(self, digits: str) -> bool:
        """Modulo 10 Prüfziffern-Validierung für GTIN"""
        total = 0
        for i, digit in enumerate(digits[:-1]):
            weight = 3 if i % 2 == len(digits) % 2 else 1
            total += int(digit) * weight
        check = (10 - (total % 10)) % 10
        return check == int(digits[-1])
```

---

## Bilder-Storage

### Storage-Abstraktion

```python
from abc import ABC, abstractmethod

class ImageStorage(ABC):
    """Abstrakte Basis für Bilder-Speicherung"""
    
    @abstractmethod
    def save(self, file: UploadFile, path: str) -> str:
        """Speichert Bild, gibt URL/Pfad zurück"""
        pass
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        """Löscht Bild"""
        pass
    
    @abstractmethod
    def get_url(self, path: str) -> str:
        """Gibt öffentliche URL zurück"""
        pass


class LocalImageStorage(ImageStorage):
    """MVP: Lokale Speicherung"""
    
    def __init__(self, base_path: str = "/uploads/pim"):
        self.base_path = base_path
    
    def save(self, file: UploadFile, path: str) -> str:
        full_path = os.path.join(self.base_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file.file.read())
        return path
    
    def get_url(self, path: str) -> str:
        return f"/static/uploads/pim/{path}"


class S3ImageStorage(ImageStorage):
    """V1: S3-kompatible Speicherung"""
    
    def __init__(self, bucket: str, endpoint: str, ...):
        self.client = boto3.client('s3', endpoint_url=endpoint, ...)
    
    def save(self, file: UploadFile, path: str) -> str:
        self.client.upload_fileobj(file.file, self.bucket, path)
        return path
    
    def get_url(self, path: str) -> str:
        return f"{self.cdn_url}/{path}"


# Factory basierend auf Einstellungen
def get_image_storage(settings: Settings) -> ImageStorage:
    if settings.image_storage_type == "s3":
        return S3ImageStorage(
            bucket=settings.s3_bucket,
            endpoint=settings.s3_endpoint,
            ...
        )
    return LocalImageStorage(settings.upload_path)
```

---

## Service-Schnittstellen für andere Plugins

```python
# v_flask_pim/services/product_service.py

class ProductService:
    """Hauptschnittstelle für Produkt-Operationen"""
    
    def __init__(self, repo: ProductRepository, image_storage: ImageStorage):
        self.repo = repo
        self.images = image_storage
    
    # === Lese-Operationen (für andere Plugins) ===
    
    def get_by_id(self, product_id: str) -> Optional[Product]:
        """Einzelnes Produkt laden"""
        pass
    
    def get_by_sku(self, sku: str) -> Optional[Product]:
        """Produkt nach Artikelnummer"""
        pass
    
    def get_by_barcode(self, barcode: str) -> Optional[Product]:
        """Produkt nach Barcode (GTIN/EAN/UPC)"""
        pass
    
    def get_by_category(
        self, 
        category_id: str, 
        active_only: bool = True,
        language: str = None
    ) -> list[Product]:
        """Alle Produkte einer Kategorie"""
        pass
    
    def search(
        self, 
        query: str, 
        limit: int = 20,
        category_id: str = None,
        active_only: bool = True
    ) -> list[Product]:
        """Volltextsuche"""
        pass
    
    def get_featured(self, limit: int = 10) -> list[Product]:
        """Hervorgehobene Produkte"""
        pass
    
    # === V1: Varianten ===
    
    def get_variants(self, parent_id: str) -> list[Product]:
        """Alle Varianten eines Eltern-Produkts"""
        pass
    
    def get_variant_matrix(self, parent_id: str) -> VariantMatrix:
        """Matrix aller Attribut-Kombinationen"""
        pass


class CategoryService:
    """Schnittstelle für Kategorie-Operationen"""
    
    def get_tree(
        self, 
        root_id: str = None, 
        active_only: bool = True,
        language: str = None
    ) -> list[CategoryNode]:
        """Hierarchischer Kategoriebaum"""
        pass
    
    def get_breadcrumb(self, category_id: str) -> list[Category]:
        """Pfad von Root zur Kategorie"""
        pass
    
    def get_children(self, parent_id: str = None) -> list[Category]:
        """Direkte Unterkategorien"""
        pass
```

---

## Verzeichnisstruktur

```
v_flask_pim/
├── __init__.py
├── plugin.py              # Plugin-Registrierung
├── models/
│   ├── __init__.py
│   ├── product.py         # Product, ProductImage
│   ├── category.py        # Category
│   ├── tax_rate.py        # TaxRate
│   ├── variant.py         # V1: VariantAttribute, VariantValue
│   └── translation.py     # V1: ProductTranslation, etc.
├── repositories/
│   ├── __init__.py
│   ├── base.py            # Repository ABC
│   ├── product_repo.py
│   ├── category_repo.py
│   └── postgres/          # PostgreSQL-Implementierungen
│       └── ...
├── services/
│   ├── __init__.py
│   ├── product_service.py
│   ├── category_service.py
│   ├── image_service.py
│   ├── barcode_service.py
│   └── import_service.py  # CSV-Import
├── api/
│   ├── __init__.py
│   ├── routes.py          # FastAPI-Router
│   └── schemas.py         # Pydantic-Schemas
├── admin/
│   ├── __init__.py
│   ├── products.py        # NiceGUI Admin-Seiten
│   ├── categories.py
│   └── components/        # Wiederverwendbare UI-Komponenten
├── storage/
│   ├── __init__.py
│   ├── base.py            # ImageStorage ABC
│   ├── local.py           # LocalImageStorage
│   └── s3.py              # V1: S3ImageStorage
└── migrations/
    └── ...                # Alembic-Migrationen
```

---

## Konfiguration

```python
# v_flask_pim/config.py

class PIMSettings(BaseSettings):
    """PIM-Plugin Einstellungen"""
    
    # Bilder
    image_storage_type: str = "local"  # 'local' oder 's3'
    upload_path: str = "/uploads/pim"
    max_image_size_mb: int = 5
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp"]
    thumbnail_sizes: list[tuple[int, int]] = [(150, 150), (400, 400)]
    
    # S3 (V1)
    s3_endpoint: str = None
    s3_bucket: str = None
    s3_access_key: str = None
    s3_secret_key: str = None
    s3_cdn_url: str = None
    
    # Mehrsprachigkeit (V1)
    default_language: str = "de"
    available_languages: list[str] = ["de", "en"]
    
    # Sonstiges
    barcode_validation: bool = True
    
    class Config:
        env_prefix = "PIM_"
```
