from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.services.mesa import MesaService
from app.schemas.schemas import MesaCreate, MesaResponse
from app.models.enums import UserRole

router = APIRouter(prefix="/mesas", tags=["Mesas"])
service = MesaService()


@router.post("/", response_model=MesaResponse, status_code=status.HTTP_201_CREATED)
def create_mesa(payload: MesaCreate, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.ADMIN]))):
    try:
        return service.create(db, payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/", response_model=list[MesaResponse])
def list_mesas(db: Session = Depends(get_db), _current_user = Depends(get_current_active_user)):  # type: ignore[unused-variable]
    return service.get_all(db)


@router.get("/disponibles", response_model=list[MesaResponse])
def get_mesas_disponibles(
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_active_user)  # type: ignore[unused-variable]
):
    return service.get_disponibles(db)



@router.get("/{mesa_id}", response_model=MesaResponse)
def get_mesa(mesa_id: int, db: Session = Depends(get_db), _current_user = Depends(get_current_active_user)):  # type: ignore[unused-variable]
    try:
        return service.get_by_id(db, mesa_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{mesa_id}")
def delete_mesa(mesa_id: int, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.ADMIN]))):
    try:
        return service.delete(db, mesa_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
