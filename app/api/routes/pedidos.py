from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.services.pedido import PedidoService
from app.schemas.schemas import (
    PedidoCreate, 
    PedidoResponse, 
    PedidoUpdate, 
    DetallePedidoCreate, 
    DetallePedidoResponse,
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
        # 🔥 Pasamos mesa_id y el ID del usuario que viene del TOKEN
        return service.create(db, mesa_id=payload.mesa_id, current_user_id=current_user.id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

#nuevo endpoint para listar pedidos con lógica de roles

@router.get("/", response_model=list[PedidoResponse])
def list_pedidos(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    # 👨‍🍳 COCINA: Solo lo pendiente por preparar
    if current_user.rol == UserRole.COCINA:
        return service.get_pedidos_cocina(db)
    
    # 🏃 MESERO: Solo sus pedidos activos
    if current_user.rol == UserRole.MESERO:
        return service.get_pedidos_by_usuario(db, usuario_id=current_user.id)
    
    # 👑 ADMIN: Todo el historial
    return service.get_all(db)

@router.get("/", response_model=list[PedidoResponse])
def list_pedidos(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    return service.get_all(db)


@router.get("/{pedido_id}", response_model=PedidoResponse)
def get_pedido(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        return service.get_by_id(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/{pedido_id}", response_model=PedidoResponse)
def update_pedido(
    pedido_id: int, 
    payload: PedidoUpdate, 
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))
):
    try:
        return service.update(db, pedido_id, payload.model_dump(exclude_unset=True))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{pedido_id}")
def delete_pedido(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.ADMIN]))):
    try:
        return service.delete(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{pedido_id}/detalles", response_model=DetallePedidoResponse, status_code=status.HTTP_201_CREATED)
def add_detalle(
    pedido_id: int, 
    payload: DetallePedidoCreate, 
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))
):
    try:
        # 🔥 Usamos los parámetros limpios del service
        return service.add_detalle(
            db, 
            pedido_id=pedido_id, 
            producto_id=payload.producto_id, 
            cantidad=payload.cantidad
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{pedido_id}/cerrar", response_model=PedidoResponse)
def cerrar_pedido(
    pedido_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))
):
    try:
        return service.cerrar_pedido(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{pedido_id}/pago", response_model=PagoResponse)
def create_pago(
    pedido_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.MESERO]))
):
    try:
        return service.create_pago(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{pedido_id}/total")
def get_total(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    return {"total": service.calculate_pago_total(db, pedido_id)}