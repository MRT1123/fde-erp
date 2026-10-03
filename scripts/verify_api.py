"""基础模块 API 冒烟测试：物料/供应商/库存/看板（本地 SQLite）。"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "erp-backend"))

import httpx

from app.core.database import Base, engine
from app.main import app

BASE = "http://test"


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url=BASE) as c:
        # 物料
        r = await c.post("/api/v1/materials", json={"code": "M001", "name": "服务器", "category": "硬件", "unit": "台", "default_price": 12000})
        assert r.status_code == 201, r.text
        mat = r.json()
        print(f"[物料] 创建 id={mat['id']} name={mat['name']}")

        r = await c.put(f"/api/v1/materials/{mat['id']}", json={"spec": "2U", "default_price": 11800})
        assert r.status_code == 200 and r.json()["spec"] == "2U", r.text
        print(f"[物料] 更新 -> spec={r.json()['spec']} price={r.json()['default_price']}")

        r = await c.get(f"/api/v1/materials/{mat['id']}")
        assert r.status_code == 200, r.text
        print(f"[物料] 详情 -> {r.json()['code']}")

        # 供应商
        r = await c.post("/api/v1/suppliers", json={"name": "华为云", "contact_person": "张三", "phone": "13800000000"})
        assert r.status_code == 201, r.text
        sup = r.json()
        print(f"[供应商] 创建 id={sup['id']} code={sup['code']} first_cooperation={sup['first_cooperation']}")

        r = await c.put(f"/api/v1/suppliers/{sup['id']}", json={"qualification_status": "verified", "credit_score": 92})
        assert r.status_code == 200 and r.json()["qualification_status"] == "verified", r.text
        print(f"[供应商] 更新 -> 资质={r.json()['qualification_status']} 信用={r.json()['credit_score']}")

        # 库存
        r = await c.post("/api/v1/inventory/changes", json={"material_id": mat["id"], "movement_type": "in", "quantity": 100, "remark": "期初入库"})
        assert r.status_code == 201, r.text
        print(f"[库存] 入库 id={r.json()['id']}")

        r = await c.post("/api/v1/inventory/changes", json={"material_id": mat["id"], "movement_type": "out", "quantity": 30, "remark": "领用"})
        assert r.status_code == 201, r.text

        invs = (await c.get("/api/v1/inventory")).json()
        inv = next(i for i in invs if i["material_id"] == mat["id"])
        assert inv["quantity"] == 70, inv
        print(f"[库存] 出库后可用={inv['quantity']}")

        # 看板
        r = await c.get("/api/v1/dashboard/summary")
        assert r.status_code == 200, r.text
        print(f"[看板] summary -> {r.json()}")

        r = await c.get("/api/v1/dashboard/supplier-risk")
        assert r.status_code == 200, r.text
        print(f"[看板] supplier-risk -> {r.json()}")

        r = await c.get("/api/v1/dashboard/status-distribution")
        assert r.status_code == 200, r.text
        print(f"[看板] status-distribution -> {r.json()}")

    await engine.dispose()
    print("\n=== 基础模块 API 冒烟测试全部通过 ===")


if __name__ == "__main__":
    asyncio.run(main())
