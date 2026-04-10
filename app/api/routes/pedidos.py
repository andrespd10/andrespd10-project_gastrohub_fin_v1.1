from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.services.pedido import PedidoService
from app.schemas.schemas import (
    PedidoCreate, 
    PedidoResponse, 
    PedidoUpdateItems,
    DetallePedidoBulkCreate,
    PagoResponse
)
from app.models.enums import UserRole

router = APIRouter(prefix="/pedidos", tags=["Pedidos - Gestión de Órdenes"])
service = PedidoService()


@router.post("/", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def create_pedido(
    payload: PedidoCreate, 
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))
):
    """
    📋 Crear un pedido completo en una sola acción
    
    El mesero proporciona:
    - **mesa_id**: Número de mesa (pasará a estado OCUPADA)
    - **items**: Lista de productos con cantidad y notas especiales
    
    El pedido se crea automáticamente con estado ABIERTO.
    """
    try:
        return service.create(
            db, 
            mesa_id=payload.mesa_id, 
            current_user_id=current_user.id,
            items=payload.items
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.get("/", response_model=list[PedidoResponse])
def list_pedidos(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    """
    📊 Listar pedidos según el rol del usuario
    
    - **COCINA**: Solo pedidos ABIERTOS para preparar
    - **MESERO**: Solo sus pedidos (creados por él)
    - **ADMIN**: Historial completo de todos los pedidos
    """
    if current_user.rol == UserRole.COCINA:
        return service.get_pedidos_cocina(db)
    
    if current_user.rol == UserRole.MESERO:
        return service.get_pedidos_by_usuario(db, usuario_id=current_user.id)
    
    return service.get_all(db)


@router.get("/{pedido_id}", response_model=PedidoResponse)
def get_pedido(
    pedido_id: int, 
    db: Session = Depends(get_db), 
    _current_user = Depends(get_current_active_user)  # type: ignore[unused-variable]
):
    """
    🔍 Obtener detalles completos de un pedido
    
    Retorna:
    - Mesa y datos del mesero
    - Todos los items/platos con cantidad, precio y notas
    - Estado actual del pedido
    """
    try:
        return service.get_by_id(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{pedido_id}")
def delete_pedido(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.ADMIN, UserRole.MESERO]))):
    """
    🗑️ Eliminar un pedido completo
    
    Solo se puede eliminar pedidos en estado ABIERTO.
    La mesa se libera automáticamente.
    """
    try:
        return service.delete(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{pedido_id}/items", response_model=dict)
def update_pedido_items(
    pedido_id: int, 
    payload: PedidoUpdateItems,
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))
):
    """
    ✏️ Editar items de un pedido abierto
    
    El mesero puede:
    - **Cambiar cantidad** de un plato
    - **Actualizar notas** especiales (sin cebolla, extra picante, etc)
    - **Eliminar items** (enviando cantidad = 0)
    
    Ejemplo:
    ```json
    {
      "items": [
        {"detalle_id": 5, "cantidad": 2, "descripcion": "Sin cebolla"},
        {"detalle_id": 6, "cantidad": 0}  // Esto lo elimina
      ]
    }
    ```
    """
    try:
        return service.update_items(db, pedido_id, payload.items)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

#  AGREGAR MÁS PRODUCTOS A UN PEDIDO ABIERTO
@router.post("/{pedido_id}/detalles", status_code=status.HTTP_201_CREATED)
def add_detalles_masivos(
    pedido_id: int, 
    payload: DetallePedidoBulkCreate,
    db: Session = Depends(get_db), 
    current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))
):
    """
    ➕ Agregar más productos a un pedido ya abierto
    
    Útil cuando el cliente ordena algo más durante la cena.
    Solo funciona con pedidos en estado ABIERTO.
    """
    try:
        return service.add_multiple_detalles(
            db, 
            pedido_id=pedido_id, 
            items=payload.items,
            usuario_id=current_user.id
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{pedido_id}/cerrar", response_model=PedidoResponse)
def cerrar_pedido(
    pedido_id: int, 
    db: Session = Depends(get_db), 
    _current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))  # type: ignore[unused-variable]
):
    """
    ✅ Cerrar un pedido (cocina finaliza la preparación)
    
    Cambios:
    - Pedido pasa a estado CERRADO
    - Mesa se libera (pasa a LIBRE)
    - Ya no se pueden hacer modificaciones
    """
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
    """
    💳 Procesar el pago de un pedido
    
    Requisitos:
    - El pedido debe estar CERRADO
    - No puede tener un pago registrado previamente
    - Se calcula suma automática de todos los items
    """
    try:
        return service.create_pago(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


