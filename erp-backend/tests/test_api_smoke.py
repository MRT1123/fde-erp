"""API smoke tests aligned with real endpoints (materials/suppliers/inventory/dashboard)."""
import logging

import httpx
import pytest

logging.disable(logging.CRITICAL)

from app.core.database import AsyncSessionLocal, Base, engine
from app import models  # noqa: F401
from app.main import app
from app.models.supplier import Supplier
from app.models.org import Department


@pytest.fixture(autouse=True)
async def _db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        dept = Department(code="DP-IT", name="IT Dept")
        sup = Supplier(code="SUP-A", name="Supplier A", contact_person="Zhang San", phone="10086")
        db.add_all([dept, sup])
        await db.commit()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_material_crud():
    async with await _client() as c:
        r = await c.post("/api/v1/materials", json={
            "code": "MAT-001", "name": "Test Material", "category": "office",
            "spec": "X-1", "unit": "pcs",
        })
        assert r.status_code == 201, r.text
        mid = r.json()["id"]
        r = await c.get(f"/api/v1/materials/{mid}")
        assert r.status_code == 200
        r = await c.get("/api/v1/materials")
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_supplier_list_and_update():
    async with await _client() as c:
        r = await c.get("/api/v1/suppliers")
        assert r.status_code == 200
        sid = r.json()[0]["id"]
        r = await c.put(f"/api/v1/suppliers/{sid}", json={"qualification_status": "verified"})
        assert r.status_code == 200, r.text
        assert r.json()["qualification_status"] == "verified"


@pytest.mark.asyncio
async def test_inventory_stock_in_out():
    async with await _client() as c:
        r = await c.post("/api/v1/materials", json={
            "code": "MAT-002", "name": "Stock Material", "category": "office",
            "spec": "S-1", "unit": "pcs",
        })
        assert r.status_code == 201, r.text
        mid = r.json()["id"]
        r = await c.post("/api/v1/inventory/changes", json={
            "material_id": mid, "movement_type": "in", "quantity": 100, "warehouse": "Main",
        })
        assert r.status_code == 201, r.text
        r = await c.post("/api/v1/inventory/changes", json={
            "material_id": mid, "movement_type": "out", "quantity": 30, "warehouse": "Main",
        })
        assert r.status_code == 201, r.text
        r = await c.get("/api/v1/inventory")
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == 70


@pytest.mark.asyncio
async def test_dashboard_stats():
    async with await _client() as c:
        r = await c.get("/api/v1/dashboard/summary")
        assert r.status_code == 200
        assert "total_requests" in r.json()
        r = await c.get("/api/v1/dashboard/risk-distribution")
        assert r.status_code == 200
