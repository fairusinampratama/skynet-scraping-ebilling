from fastapi.testclient import TestClient
from main import app
from database import Base, engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

# Create a clean test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ebilling.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    # Setup step
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown step
    Base.metadata.drop_all(bind=engine)

def populate_test_db():
    from models import Area, Package, Customer
    db = TestingSessionLocal()
    area = Area(name="TEST_AREA", code="T_CODE")
    pkg = Package(name="TEST_PKG", price=10000)
    db.add(area)
    db.add(pkg)
    db.flush()
    
    cust = Customer(
        id="CUST_001", code="C01", name="Test Customer",
        status="active", is_online=True,
        package_id=pkg.id, area_id=area.id
    )
    db.add(cust)
    db.commit()
    db.close()

def test_get_areas_empty():
    response = client.get("/api/v1/areas")
    assert response.status_code == 200
    assert response.json() == []

def test_customers_payload_schema():
    populate_test_db()
    response = client.get("/api/v1/customers")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    cust = data[0]
    
    # Assert Root Keys
    assert cust["id"] == "CUST_001"
    assert cust["name"] == "Test Customer"
    assert cust["status"] == "active"
    assert cust["is_online"] is True
    
    # Assert Nested Relations Strategy
    assert "package" in cust
    assert cust["package"]["name"] == "TEST_PKG"
    assert cust["package"]["price"] == 10000
    
    assert "area" in cust
    assert cust["area"]["name"] == "TEST_AREA"
    assert cust["area"]["code"] == "T_CODE"

def test_sync_trigger_auth_denied():
    response = client.post("/api/v1/sync/trigger")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API Key"}

def test_sync_trigger_auth_granted(monkeypatch):
    # Mock sync.run_sync to avoid real scraping
    import sync
    def dummy_sync():
        pass
    monkeypatch.setattr(sync, "run_sync", dummy_sync)
    
    # Override the API Key dependency logic instead of env var
    from main import verify_api_key
    def override_verify_api_key():
        return True
    
    app.dependency_overrides[verify_api_key] = override_verify_api_key
    
    response = client.post("/api/v1/sync/trigger")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Manual sync triggered and finished."}
    
    # Cleanup dependency override
    del app.dependency_overrides[verify_api_key]
