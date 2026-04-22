from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.services.pago import PagoService
from app.schemas.schemas import PagoResponse
from app.models.enums import UserRole

router = APIRouter(prefix="/pagos", tags=["Pagos - Historial"])
service = PagoService()


@router.get("/filtrar", response_model=list[PagoResponse])
def filter_pagos_by_date(
    fecha_inicio: date = Query(..., description="Fecha de inicio del rango (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del rango (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    _current_user = Depends(require_role([UserRole.ADMIN])),  # type: ignore[unused-variable]
):
    """
    Filtrar pagos por rango de fechas

    **Solo ADMIN** puede filtrar el historial de pagos.

    - **fecha_inicio**: Fecha de inicio del rango en formato `YYYY-MM-DD`
    - **fecha_fin**: Fecha de fin del rango en formato `YYYY-MM-DD`

    Retorna todos los pagos registrados dentro del rango indicado, ordenados de más reciente a más antiguo.
    """
    try:
        return service.filter_by_date_range(db, fecha_inicio, fecha_fin)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/", response_model=list[PagoResponse])
def list_pagos(
    db: Session = Depends(get_db), 
    _current_user = Depends(require_role([UserRole.ADMIN]))  # type: ignore[unused-variable]
):
    """
    Listar todos los pagos registrados
    
    **Solo ADMIN** puede ver el historial completo de transacciones.
    """
    return service.get_all(db)


@router.get("/{pago_id}", response_model=PagoResponse)
def get_pago(
    pago_id: int, 
    db: Session = Depends(get_db), 
    _current_user = Depends(require_role([UserRole.ADMIN]))  # type: ignore[unused-variable]
):
    """
    Obtener detalles de un pago específico
    
    Muestra monto total, fecha y pedido asociado.
    """
    try:
        return service.get_by_id(db, pago_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))