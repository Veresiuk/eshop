from sqlalchemy.orm import Session
from eshop.models import Product, Category
from eshop.repositories import ProductRepository, CategoryRepository
from eshop.schemas import (
    ProductCreate,
    ProductUpdate,
    CategoryCreate,
    PurchaseResponse,
    InventoryStats,
    ProductResponse,
)


class InventoryService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.product_repo = ProductRepository(session)
        self.category_repo = CategoryRepository(session)

    def create_category(self, data: CategoryCreate) -> Category:
        existing = self.category_repo.get_by_name(data.name)
        if existing:
            raise ValueError(f"Category '{data.name}' already exists")
        cat = Category(name=data.name, description=data.description)
        return self.category_repo.add(cat)

    def get_all_categories(self) -> list[Category]:
        return self.category_repo.get_all()

    def get_category_by_id(self, category_id: int) -> Category | None:
        return self.category_repo.get_by_id(category_id)

    def create_product(self, data: ProductCreate) -> Product:
        category = self.category_repo.get_by_id(data.category_id)
        if not category:
            raise ValueError(f"Category with ID {data.category_id} not found")
        prod = Product(
            name=data.name,
            description=data.description,
            price=data.price,
            stock=data.stock,
            category_id=data.category_id,
        )
        return self.product_repo.add(prod)

    def get_product_by_id(self, product_id: int) -> Product | None:
        return self.product_repo.get_by_id(product_id)

    def search_products(
        self,
        query: str | None = None,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        return self.product_repo.get_all(
            query=query,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            skip=skip,
            limit=limit,
        )

    def get_products_by_category(self, category_id: int) -> list[Product]:
        if not self.category_repo.get_by_id(category_id):
            raise KeyError(f"Category with ID {category_id} not found")
        return self.product_repo.get_by_category_id(category_id)

    def update_product(self, product_id: int, data: ProductUpdate) -> Product | None:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return None

        if data.category_id is not None:
            cat = self.category_repo.get_by_id(data.category_id)
            if not cat:
                raise ValueError(f"Category with ID {data.category_id} not found")

        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(product, field, value)

        return self.product_repo.update(product)

    def delete_product(self, product_id: int) -> bool:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return False
        self.product_repo.delete(product)
        return True

    def purchase_product(self, product_id: int, quantity: int) -> PurchaseResponse:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise KeyError(f"Product with ID {product_id} not found")

        if product.stock < quantity:
            raise ValueError(
                f"Insufficient stock for '{product.name}'. Requested: {quantity}, Available: {product.stock}"
            )

        # Транзакційне списання кількості
        product.stock -= quantity
        total = round(product.price * quantity, 2)
        self.session.commit()
        self.session.refresh(product)

        return PurchaseResponse(
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            unit_price=product.price,
            total_amount=total,
            remaining_stock=product.stock,
            message="Purchase successful",
        )

    def get_inventory_stats(self) -> InventoryStats:
        count = self.product_repo.get_products_count()
        total_items = self.product_repo.get_total_stock_count()
        val = round(self.product_repo.get_total_inventory_value(), 2)
        most_expensive = self.product_repo.get_most_expensive()

        most_exp_resp = (
            ProductResponse.model_validate(most_expensive) if most_expensive else None
        )

        return InventoryStats(
            total_products_count=count,
            total_items_in_stock=total_items,
            total_inventory_value=val,
            most_expensive_product=most_exp_resp,
        )