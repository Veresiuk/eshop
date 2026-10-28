from sqlalchemy import select, func
from sqlalchemy.orm import Session
from eshop.models import Product, Category


class CategoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(self) -> list[Category]:
        stmt = select(Category).order_by(Category.name)
        return list(self.session.scalars(stmt))

    def get_by_id(self, category_id: int) -> Category | None:
        return self.session.get(Category, category_id)

    def get_by_name(self, name: str) -> Category | None:
        stmt = select(Category).where(Category.name == name)
        return self.session.scalars(stmt).first()

    def add(self, category: Category) -> Category:
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.session.delete(category)
        self.session.commit()


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(
        self,
        query: str | None = None,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        stmt = select(Product)
        if query:
            stmt = stmt.where(Product.name.ilike(f"%{query}%"))
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        stmt = stmt.offset(skip).limit(limit)
        return list(self.session.scalars(stmt))

    def get_by_id(self, product_id: int) -> Product | None:
        return self.session.get(Product, product_id)

    def get_by_category_id(self, category_id: int) -> list[Product]:
        stmt = select(Product).where(Product.category_id == category_id).order_by(Product.name)
        return list(self.session.scalars(stmt))

    def add(self, product: Product) -> Product:
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def update(self, product: Product) -> Product:
        self.session.commit()
        self.session.refresh(product)
        return product

    def delete(self, product: Product) -> None:
        self.session.delete(product)
        self.session.commit()

    def get_most_expensive(self) -> Product | None:
        stmt = select(Product).order_by(Product.price.desc()).limit(1)
        return self.session.scalars(stmt).first()

    def get_total_inventory_value(self) -> float:
        stmt = select(func.coalesce(func.sum(Product.price * Product.stock), 0.0))
        val = self.session.scalar(stmt)
        return float(val) if val is not None else 0.0

    def get_total_stock_count(self) -> int:
        stmt = select(func.coalesce(func.sum(Product.stock), 0))
        val = self.session.scalar(stmt)
        return int(val) if val is not None else 0

    def get_products_count(self) -> int:
        stmt = select(func.count(Product.id))
        val = self.session.scalar(stmt)
        return int(val) if val is not None else 0