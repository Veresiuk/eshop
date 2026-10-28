from pydantic import BaseModel, Field, ConfigDict


# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str = Field(min_length=2, max_length=100, description="Назва категорії")
    description: str | None = Field(default=None, max_length=255, description="Опис категорії")


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Product Schemas ---
class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=150, description="Назва товару")
    description: str | None = Field(default=None, max_length=500, description="Опис товару")
    price: float = Field(gt=0, description="Ціна товару повинна бути строго більшою за 0")
    stock: int = Field(ge=0, description="Кількість на складі (>= 0)")
    category_id: int = Field(gt=0, description="Ідентифікатор категорії")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    category_id: int | None = Field(default=None, gt=0)


class ProductResponse(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Purchase & Stats Schemas ---
class PurchaseRequest(BaseModel):
    quantity: int = Field(gt=0, description="Кількість товару для покупки")


class PurchaseResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_amount: float
    remaining_stock: int
    message: str


class InventoryStats(BaseModel):
    total_products_count: int
    total_items_in_stock: int
    total_inventory_value: float
    most_expensive_product: ProductResponse | None


class BatchProductRequest(BaseModel):
    product_ids: list[int] = Field(min_length=1, description="Список ID товарів")