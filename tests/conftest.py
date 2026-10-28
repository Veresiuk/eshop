import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from eshop.database import Base, get_session
from eshop.api import app
from eshop.models import Category, Product

# StaticPool гарантує, що in-memory SQLite база зберігає стан між сесіями в межах тестів
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# Підміняємо залежність бази даних у FastAPI на тестову
app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(autouse=True)
def setup_database():
    # Створюємо таблиці перед кожним тестом
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Початкові дані
    cat1 = Category(name="Ноутбуки", description="Лептопи та ультрабуки")
    cat2 = Category(name="Смартфони", description="Мобільні телефони")
    session.add_all([cat1, cat2])
    session.commit()

    prod1 = Product(name="MacBook Pro 16", description="M3 Max 36GB", price=120000.0, stock=5, category_id=cat1.id)
    prod2 = Product(name="Asus ROG Zephyrus", description="Ryzen 9 RTX 4080", price=95000.0, stock=8, category_id=cat1.id)
    prod3 = Product(name="iPhone 15 Pro", description="Titanium 256GB", price=48000.0, stock=15, category_id=cat2.id)
    session.add_all([prod1, prod2, prod3])
    session.commit()
    session.close()

    yield

    # Очищаємо таблиці після завершення тесту
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac