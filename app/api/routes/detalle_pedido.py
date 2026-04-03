from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.services.detalle_pedido import DetallePedidoService
from app.schemas.schemas import DetallePedidoResponse, DetallePedidoUpdate
from app.models.enums import UserRole

router = APIRouter(prefix="/detalle_pedidos", tags=["Detalle Pedidos"])
service = DetallePedidoService()


@router.get("/", response_model=list[DetallePedidoResponse])
def list_detalles(db: Session = Depends(get_db), _current_user = Depends(get_current_active_user)):  # type: ignore[unused-variable]
    return service.get_all(db)


@router.get("/{detalle_id}", response_model=DetallePedidoResponse)
def get_detalle(detalle_id: int, db: Session = Depends(get_db), _current_user = Depends(get_current_active_user)):  # type: ignore[unused-variable]
    try:
        return service.get_by_id(db, detalle_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{detalle_id}", response_model=DetallePedidoResponse)
def update_detalle(detalle_id: int, payload: DetallePedidoUpdate, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.COCINA, UserRole.MESERO]))):
    try:
        return service.update(db, detalle_id, payload.model_dump(exclude_unset=True))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{detalle_id}")
def delete_detalle(detalle_id: int, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.COCINA, UserRole.MESERO, UserRole.ADMIN]))):
    try:
        return service.delete(db, detalle_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
