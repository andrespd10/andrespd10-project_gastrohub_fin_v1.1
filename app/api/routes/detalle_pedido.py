from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_active_user, require_role
from app.services.detalle_pedido import DetallePedidoService
from app.schemas.schemas import DetallePedidoResponse, DetallePedidoUpdate
from app.models.enums import UserRole

# El tag ahora refleja que es la vista de trabajo del cocinero
router = APIRouter(prefix="/detalle-pedidos", tags=["Producción - Vista de Cocina"])
service = DetallePedidoService()


@router.get("/", response_model=List[DetallePedidoResponse])
def list_detalles(
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.COCINA, UserRole.ADMIN]))
):
    """
    **LISTA DE TRABAJO (COCINA)**
    
    Este endpoint devuelve exclusivamente los platos que están **PENDIENTES** o en **PREPARACIÓN**. Una vez marcados como LISTO, desaparecen de aquí.
    """
    return service.get_all(db)


@router.get("/pedido/{pedido_id}", response_model=List[DetallePedidoResponse])
def list_detalles_por_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_active_user)
):
    """
    **PRODUCTOS DE UN PEDIDO**

    Devuelve todos los ítems (productos) asociados a un `pedido_id` específico,
    sin importar su estado. Útil para la vista de detalle de un pedido en cocina o en sala.
    """
    return service.get_by_pedido(db, pedido_id)


@router.get("/{detalle_id}", response_model=DetallePedidoResponse)
def get_detalle(
    detalle_id: int, 
    db: Session = Depends(get_db), 
    _current_user = Depends(get_current_active_user)
):
    """
    Obtener información técnica de un ítem específico.
    """
    try:
        return service.get_by_id(db, detalle_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{detalle_id}", response_model=DetallePedidoResponse)
def update_detalle(
    detalle_id: int, 
    payload: DetallePedidoUpdate, 
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.COCINA]))
):
    """
    **ACTUALIZAR PROGRESO (SOLO COCINA)**
    
    Permite al cocinero cambiar el estado del plato:
    - De **PENDIENTE**  **PREPARANDO**
    - De **PREPARANDO**  **LISTO**
    
    *Nota: Si el pedido ya fue pagado/cerrado, no permitirá cambios.*
    """
    try:
        return service.update(db, detalle_id, payload.model_dump(exclude_unset=True))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{detalle_id}")
def delete_detalle(
    detalle_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))
):
    """
    **ELIMINAR ÍTEM**
    
    Solo permitido para Meseros/Admin si hubo un error en la orden y el pedido sigue ABIERTO.
    """
    try:
        return service.delete(db, detalle_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))