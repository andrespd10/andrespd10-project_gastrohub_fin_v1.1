from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.services.pago import PagoService
from app.schemas.schemas import PagoResponse
from app.models.enums import UserRole

router = APIRouter(prefix="/pagos", tags=["Pagos"])
service = PagoService()


@router.get("/", response_model=list[PagoResponse])
def list_pagos(db: Session = Depends(get_db), _current_user = Depends(require_role([UserRole.ADMIN]))):  # type: ignore[unused-variable]
    return service.get_all(db)


@router.get("/{pago_id}", response_model=PagoResponse)
def get_pago(pago_id: int, db: Session = Depends(get_db), _current_user = Depends(require_role([UserRole.ADMIN]))):  # type: ignore[unused-variable]
    try:
        return service.get_by_id(db, pago_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))