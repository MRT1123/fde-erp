"""物料 API。"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.material import Material
from app.schemas.material import MaterialCreate, MaterialOut, MaterialUpdate

router = APIRouter()


@router.get("", response_model=list[MaterialOut])
async def list_materials(db: DbSession, page: int = 1, page_size: int = 20):
    result = await db.execute(select(Material).order_by(Material.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all()


@router.post("", response_model=MaterialOut, status_code=201)
async def create_material(payload: MaterialCreate, db: DbSession):
    obj = Material(**payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/{material_id}", response_model=MaterialOut)
async def get_material(material_id: int, db: DbSession):
    result = await db.execute(select(Material).where(Material.id == material_id))
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="物料不存在")
    return obj


@router.put("/{material_id}", response_model=MaterialOut)
async def update_material(material_id: int, payload: MaterialUpdate, db: DbSession):
    obj = await db.get(Material, material_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="物料不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.commit()
    await db.refresh(obj)
    return obj
