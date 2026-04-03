from sqlalchemy.orm import Session

from app.models import Usuario
from app.models.enums import UserRole
from app.repositories import UsuarioRepository
from app.services.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.core.security import get_password_hash


class UsuarioService:
    def __init__(self, repository: UsuarioRepository = None):
        self.repo = repository or UsuarioRepository()

    # ------------------------
    # CREAR USUARIO
    # ------------------------
    def create(self, db: Session, payload: dict, actor_role: UserRole = None) -> Usuario:
        """
        🔐 CREACIÓN DE USUARIO

        CASO 1: Registro público (actor_role=None)
            → SOLO permite ADMIN

        CASO 2: Creación interna
            → SOLO ADMIN puede crear usuarios
            → ADMIN SOLO puede crear MESERO o COCINA
            → ADMIN NO puede crear ADMIN
        """

        # 🟢 REGISTRO PÚBLICO
        if actor_role is None:
            if payload.get("rol") != UserRole.ADMIN:
                raise ForbiddenError("Solo se permite registro como ADMIN")

        # 🔐 CREACIÓN INTERNA
        else:
            if actor_role != UserRole.ADMIN:
                raise ForbiddenError("Solo un administrador puede crear usuarios")

        ## solo se puede crear MESERO o COCINA
            if payload.get("rol") == UserRole.ADMIN:
                raise ForbiddenError("No se pueden crear más administradores")

        # VALIDAR EMAIL
        existing = self.repo.get_by_email(db, payload["email"])
        if existing:
            raise BadRequestError("El email ya está registrado")

        # HASH PASSWORD
        payload["password"] = get_password_hash(payload["password"])

        usuario = self.repo.create(db, payload)
        db.commit()
        return usuario

    # ------------------------
    # OBTENER POR ID
    # ------------------------
    def get_by_id(self, db: Session, usuario_id: int, current_user: Usuario):
        """
        🔐 SEGURIDAD:
        - ADMIN → puede ver cualquiera
        - Usuario normal → solo su propio perfil
        """
        usuario = self.repo.get_by_id(db, usuario_id)

        if not usuario:
            raise NotFoundError("Usuario no encontrado")

        if current_user.rol != UserRole.ADMIN and current_user.id != usuario_id:
            raise ForbiddenError("No tienes permiso para ver este usuario")

        return usuario

    # ------------------------
    # LISTAR USUARIOS
    # ------------------------
    def get_all(self, db: Session, skip: int = 0, limit: int = 100, actor_role: UserRole = None):
        """
        🔐 SOLO ADMIN puede listar usuarios
        """
        if actor_role != UserRole.ADMIN:
            raise ForbiddenError("No tienes permisos para listar usuarios")

        return self.repo.get_all(db, skip=skip, limit=limit)

    # ------------------------
    # ACTUALIZAR USUARIO
    # ------------------------
    def update(self, db: Session, usuario_id: int, payload: dict, current_user: Usuario) -> Usuario:
        """
        REGLAS:
        - ADMIN puede actualizar cualquiera
        - Usuario solo puede actualizarse a sí mismo
        - SOLO ADMIN puede cambiar rol
        - NADIE puede asignar ADMIN
        """

        usuario = self.repo.get_by_id(db, usuario_id)

        if not usuario:
            raise NotFoundError("Usuario no encontrado")

        # 🔐 Validar permisos
        if current_user.rol != UserRole.ADMIN and current_user.id != usuario_id:
            raise ForbiddenError("No puedes modificar este usuario")

        # VALIDAR EMAIL
        if "email" in payload:
            existing = self.repo.get_by_email(db, payload["email"])
            if existing and existing.id != usuario_id:
                raise BadRequestError("El email ya está en uso")

        # HASH PASSWORD
        if "password" in payload and payload["password"]:
            payload["password"] = get_password_hash(payload["password"])

        # 🔐 CAMBIO DE ROL
        if "rol" in payload:
            if current_user.rol != UserRole.ADMIN:
                raise ForbiddenError("Solo ADMIN puede cambiar roles")

            if payload["rol"] == UserRole.ADMIN:
                raise ForbiddenError("No se puede asignar rol ADMIN")

        usuario = self.repo.update(db, usuario, payload)
        db.commit()
        return usuario

    # ------------------------
    # ELIMINAR USUARIO
    # ------------------------
    def delete(self, db: Session, usuario_id: int, current_user: Usuario):
        """
        REGLAS:
        - ADMIN → eliminación física
        - Usuario → solo puede desactivarse a sí mismo
        """

        usuario = self.repo.get_by_id(db, usuario_id)

        if not usuario:
            raise NotFoundError("Usuario no encontrado")

        # NO ADMIN
        if current_user.rol != UserRole.ADMIN:
            if current_user.id != usuario_id:
                raise ForbiddenError("No puedes eliminar otros usuarios")

            usuario = self.repo.update(db, usuario, {"activo": False})
            db.commit()
            return usuario

        # ADMIN → eliminación física
        deleted = self.repo.delete(db, usuario_id)

        db.commit()
        return deleted

    # ------------------------
    # GET POR EMAIL
    # ------------------------
    def get_by_email(self, db: Session, email: str) -> Usuario:
        return self.repo.get_by_email(db, email)