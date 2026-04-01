from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.services.producto import ProductoService
from app.schemas.schemas import ProductoCreate, ProductoResponse, ProductoUpdate
from app.models.enums import UserRole

router = APIRouter(prefix="/productos", tags=["Productos"])
service = ProductoService()


@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def create_producto(payload: ProductoCreate, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.ADMIN]))):
    try:
        return service.create(db, payload.dict())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/", response_model=list[ProductoResponse])
def list_productos(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    return service.get_all(db)


@router.get("/{producto_id}", response_model=ProductoResponse)
def get_producto(producto_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        return service.get_by_id(db, producto_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/{producto_id}", response_model=ProductoResponse)
def update_producto(producto_id: int, payload: ProductoUpdate, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.ADMIN]))):
    try:
        return service.update(db, producto_id, payload.dict(exclude_unset=True))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{producto_id}")
def delete_producto(producto_id: int, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.ADMIN]))):
    try:
        return service.delete(db, producto_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
