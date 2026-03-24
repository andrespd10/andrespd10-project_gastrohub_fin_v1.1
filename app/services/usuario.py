from sqlalchemy.orm import Session

from app.models import Usuario
from app.models.enums import UserRole
from app.repositories import UsuarioRepository
from app.services.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.core.security import get_password_hash


class UsuarioService:
    def __init__(self, repository: UsuarioRepository = None):
        self.repo = repository or UsuarioRepository()

    def create(self, db: Session, payload: dict) -> Usuario:
        # Validar email único
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

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return self.repo.get_all(db, skip=skip, limit=limit)

    def update(self, db: Session, usuario_id: int, payload: dict, actor_role: UserRole = None) -> Usuario:
        usuario = self.get_by_id(db, usuario_id)

        # Validar email único
        if "email" in payload:
            existing = self.repo.get_by_email(db, payload["email"])
            if existing and existing.id != usuario_id:
                raise BadRequestError("El email ya está en uso")

        # Hash si cambian password
        if "password" in payload and payload["password"]:
            payload["password"] = get_password_hash(payload["password"])

        # Solo ADMIN puede cambiar roles
        if "rol" in payload and actor_role != UserRole.ADMIN:
            raise ForbiddenError("Solo un administrador puede cambiar el rol")

        usuario = self.repo.update(db, usuario, payload)
        db.commit()
        return usuario

    def delete(self, db: Session, usuario_id: int, actor_role: UserRole = None):
        usuario = self.get_by_id(db, usuario_id)

        if actor_role != UserRole.ADMIN:
            # Eliminación lógica
            usuario = self.repo.update(db, usuario, {"activo": False})
            db.commit()
            return usuario

        deleted = self.repo.delete(db, usuario_id)
        if not deleted:
            raise NotFoundError(f"Usuario con id {usuario_id} no encontrado")

        db.commit()
        return deleted

    def get_by_email(self, db: Session, email: str) -> Usuario:
        return self.repo.get_by_email(db, email)