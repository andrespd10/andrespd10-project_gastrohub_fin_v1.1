from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db  # 🔥 CORREGIDO: import correcto
from app.api.deps import get_current_active_user
from app.services.usuario import UsuarioService
from app.services.exceptions import ForbiddenError, BadRequestError, NotFoundError
from app.schemas.schemas import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.models import Usuario  # 🔥 para tipado

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])
service = UsuarioService()


# ------------------------
# CREAR USUARIO
# ------------------------
@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def create_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)  # 🔥 protegido
):
    """
    Crear usuario.

    - SOLO ADMIN puede crear usuarios
    - ADMIN solo puede crear MESERO o COCINA
    - NO puede crear ADMIN
    """
    try:
        return service.create(
            db,
            payload.dict(),
            current_user.rol  # 🔥 clave: pasamos el rol al service
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ------------------------
# LISTAR USUARIOS
# ------------------------
@router.get("/", response_model=List[UsuarioResponse])
def list_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Listar usuarios.

    - SOLO ADMIN puede ver todos
    """
    try:
        return service.get_all(db, actor_role=current_user.rol)
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


# ------------------------
# OBTENER USUARIO
# ------------------------
@router.get("/{usuario_id}", response_model=UsuarioResponse)
def get_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener usuario por ID.
    """
    try:
        return service.get_by_id(db, usuario_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ------------------------
# ACTUALIZAR USUARIO
# ------------------------
@router.put("/{usuario_id}", response_model=UsuarioResponse)
def update_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Actualizar usuario.

    - SOLO ADMIN puede cambiar roles
    - Nadie puede asignar ADMIN
    """
    try:
        return service.update(
            db,
            usuario_id,
            payload.dict(exclude_unset=True),
            current_user.rol
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ------------------------
# ELIMINAR USUARIO
# ------------------------
@router.delete("/{usuario_id}")
def delete_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Eliminar usuario.

    - ADMIN → eliminación física
    - Otros → desactivación (soft delete)
    """
    try:
        return service.delete(db, usuario_id, current_user.rol)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc))