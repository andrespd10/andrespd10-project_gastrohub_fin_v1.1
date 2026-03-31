from sqlalchemy.orm import Session

from app.models import Usuario
from app.models.enums import UserRole
from app.repositories import UsuarioRepository
from app.services.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.core.security import get_password_hash


class UsuarioService:
    def __init__(self, repository: UsuarioRepository = None):
        self.repo = repository or UsuarioRepository()

    def create(self, db: Session, payload: dict, actor_role: UserRole = None) -> Usuario:
        """
        🔐 LÓGICA DE CREACIÓN DE USUARIO

        CASO 1: Registro público (actor_role=None)
            → SOLO puede crear ADMIN

        CASO 2: Creación interna (actor autenticado)
            → SOLO ADMIN puede crear usuarios
            → ADMIN solo puede crear MESERO o COCINA
            → ADMIN NO puede crear ADMIN
        """

        # ------------------------
        # 🟢 REGISTRO PÚBLICO
        # ------------------------
        if actor_role is None:
            if payload.get("rol") != UserRole.ADMIN:
                raise ForbiddenError("Solo se permite registro como ADMIN")

        # ------------------------
        # 🔐 CREACIÓN INTERNA
        # ------------------------
        else:
            if actor_role != UserRole.ADMIN:
                raise ForbiddenError("Solo un administrador puede crear usuarios")

            # ❌ ADMIN NO puede crear otro ADMIN
            if payload.get("rol") == UserRole.ADMIN:
                raise ForbiddenError("No se pueden crear más administradores")

        # ------------------------
        # VALIDACIONES
        # ------------------------
        existing = self.repo.get_by_email(db, payload["email"])
        if existing:
            raise BadRequestError("El email ya está registrado")

        # Hash de contraseña
        payload["password"] = get_password_hash(payload["password"])

        usuario = self.repo.create(db, payload)
        db.commit()
        return usuario

    def get_by_id(self, db: Session, usuario_id: int) -> Usuario:
        usuario = self.repo.get_by_id(db, usuario_id)
        if not usuario:
            raise NotFoundError(f"Usuario con id {usuario_id} no encontrado")
        return usuario

    def get_all(self, db: Session, skip: int = 0, limit: int = 100, actor_role: UserRole = None):
        """
        🔐 SOLO ADMIN puede listar usuarios
        """
        if actor_role != UserRole.ADMIN:
            raise ForbiddenError("No tienes permisos para listar los usuarios")

        return self.repo.get_all(db, skip=skip, limit=limit)

    def update(self, db: Session, usuario_id: int, payload: dict, actor_role: UserRole = None) -> Usuario:
        usuario = self.get_by_id(db, usuario_id)

        # Validar email único
        if "email" in payload:
            existing = self.repo.get_by_email(db, payload["email"])
            if existing and existing.id != usuario_id:
                raise BadRequestError("El email ya está en uso")

        # Hash password
        if "password" in payload and payload["password"]:
            payload["password"] = get_password_hash(payload["password"])

        # 🔐 SOLO ADMIN puede cambiar roles
        if "rol" in payload:
            if actor_role != UserRole.ADMIN:
                raise ForbiddenError("Solo un administrador puede cambiar el rol")

            # ❌ nadie puede asignar ADMIN
            if payload["rol"] == UserRole.ADMIN:
                raise ForbiddenError("No se puede asignar rol ADMIN")

        usuario = self.repo.update(db, usuario, payload)
        db.commit()
        return usuario

    def delete(self, db: Session, usuario_id: int, actor_role: UserRole = None):
        usuario = self.get_by_id(db, usuario_id)

        # 🔐 NO ADMIN → eliminación lógica
        if actor_role != UserRole.ADMIN:
            usuario = self.repo.update(db, usuario, {"activo": False})
            db.commit()
            return usuario

        # ADMIN → eliminación física
        deleted = self.repo.delete(db, usuario_id)
        if not deleted:
            raise NotFoundError(f"Usuario con id {usuario_id} no encontrado")

        db.commit()
        return deleted

    def get_by_email(self, db: Session, email: str) -> Usuario:
        return self.repo.get_by_email(db, email)