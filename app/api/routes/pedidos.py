from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.services.pedido import PedidoService
from app.schemas.schemas import (
    PedidoCreate, 
    PedidoResponse, 
    DetallePedidoBulkCreate, # 🔥 Importado para el envío masivo
    PagoResponse
)
from app.models.enums import UserRole

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])
service = PedidoService()


@router.post("/", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def create_pedido(
    payload: PedidoCreate, 
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))
):
    try:
        # Pasamos mesa_id y el ID del usuario que viene del TOKEN
        return service.create(db, mesa_id=payload.mesa_id, current_user_id=current_user.id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.get("/", response_model=list[PedidoResponse])
def list_pedidos(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    # COCINA: Solo lo pendiente por preparar
    if current_user.rol == UserRole.COCINA:
        return service.get_pedidos_cocina(db)
    
    # MESERO: Solo sus pedidos activos
    if current_user.rol == UserRole.MESERO:
        return service.get_pedidos_by_usuario(db, usuario_id=current_user.id)
    
    # ADMIN: Todo el historial
    return service.get_all(db)


@router.get("/{pedido_id}", response_model=PedidoResponse)
def get_pedido(pedido_id: int, db: Session = Depends(get_db), _current_user = Depends(get_current_active_user)):  # type: ignore[unused-variable]
    try:
        return service.get_by_id(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{pedido_id}")
def delete_pedido(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.ADMIN, UserRole.MESERO]))):
    try:
        return service.delete(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

#  ENDPOINT MODIFICADO: Ahora acepta una lista de productos
@router.post("/{pedido_id}/detalles", status_code=status.HTTP_201_CREATED, summary="Add productos al pedido")
def add_detalles_masivos(
    pedido_id: int, 
    payload: DetallePedidoBulkCreate, # 👈 Cambio de Schema a Bulk
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))
):
    """
    Agrega varios productos al pedido de una sola vez.
    Ideal para cuando el mesero toma la orden completa de la mesa.
    """
    try:
        # Llamamos al nuevo método 'add_multiple_detalles' que crearemos en el service
        return service.add_multiple_detalles(
            db, 
            pedido_id=pedido_id, 
            items=payload.items,
            usuario_id=current_user.id  # Pasamos el ID del usuario para auditoría o reglas de negocio 
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{pedido_id}/cerrar", response_model=PedidoResponse)
def cerrar_pedido(
    pedido_id: int, 
    db: Session = Depends(get_db), 
    _current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))  # type: ignore[unused-variable]
):
    try:
        return service.cerrar_pedido(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{pedido_id}/pago", response_model=PagoResponse)
def create_pago(
    pedido_id: int, 
    db: Session = Depends(get_db), 
    _current_user = Depends(require_role([UserRole.ADMIN, UserRole.MESERO]))  # type: ignore[unused-variable]
):
    try:
        return service.create_pago(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


