from sqlalchemy.orm import Session
from fastapi_mail import MessageSchema, MessageType

from app.models import Usuario
from app.models.enums import UserRole
from app.repositories import UsuarioRepository
from app.services.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.core.security import get_password_hash, verify_password, create_token, decode_token, TokenType
from app.core.mail import fastmail
from app.core.config import settings

class UsuarioService:
    def __init__(self, repository: UsuarioRepository = None):
        self.repo = repository or UsuarioRepository()

    # ------------------------
    # LOGIN
    # ------------------------
    def login(self, db: Session, email: str, password: str):
        user = self.repo.get_by_email(db, email)
        if not user or not user.activo or not verify_password(password, user.password):
            raise BadRequestError("Credenciales inválidas")
        
        token = create_token(subject=user.email, token_type=TokenType.ACCESS)
        return {"access_token": token, "token_type": "bearer"}

    # ------------------------
    # CREAR USUARIO (ADMIN puede crear cualquier rol)
    # ------------------------
    def create(self, db: Session, payload: dict, actor_role: UserRole = None) -> Usuario:
        """
        Crear usuario. Solo ADMIN puede crear usuarios de cualquier rol.
        """
        if actor_role is None:
            if payload.get("rol") != UserRole.ADMIN:
                raise ForbiddenError("Solo se permite registro como ADMIN")
        else:
            if actor_role != UserRole.ADMIN:
                raise ForbiddenError("Solo un administrador puede crear usuarios")

        existing = self.repo.get_by_email(db, payload["email"])
        if existing:
            raise BadRequestError("El email ya está registrado")

        payload["password"] = get_password_hash(payload["password"])
        usuario = self.repo.create(db, payload)
        db.commit()
        return usuario

    # ------------------------
    # RECUPERACIÓN DE CONTRASEÑA (NUEVO)
    # ------------------------
    async def send_password_reset_email(self, db: Session, email: str):
        usuario = self.repo.get_by_email(db, email)
        
        # Generamos el token siempre para evitar ataques de enumeración
        token = create_token(subject=email, token_type=TokenType.RESET)

        if usuario and usuario.activo:
            link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            
            # Formato de texto plano (sin HTML visual para cumplir con tu requerimiento)
            body = f"Hola {usuario.nombre if hasattr(usuario, 'nombre') else ''},\n\n" \
                   f"Has solicitado restablecer tu contraseña en GastroHub.\n" \
                   f"Usa el siguiente enlace para crear una nueva clave (expira en 15 min):\n\n" \
                   f"{link}\n\n" \
                   f"Si no solicitaste este cambio, puedes ignorar este mensaje."

            message = MessageSchema(
                subject="Recuperación de Contraseña - GastroHub",
                recipients=[email],
                body=body,
                subtype=MessageType.plain
            )
            await fastmail.send_message(message)
        
        return {"message": "Si el email es correcto, recibirás un enlace de recuperación."}

    def reset_password_with_token(self, db: Session, token: str, new_password: str):
        # 1. Validar el token
        decoded = decode_token(token, token_type=TokenType.RESET)
        email = decoded.get("sub")

        # 2. Buscar usuario
        user = self.repo.get_by_email(db, email)
        if not user:
            raise NotFoundError("Usuario no encontrado")

        # 3. Actualizar usando tu propio método update (ya tiene el hash de password)
        return self.update(db, user.id, {"password": new_password}, current_user=user)

    # ------------------------
    # OBTENER POR ID (Tu lógica original)
    # ------------------------
    def get_by_id(self, db: Session, usuario_id: int, current_user: Usuario):
        usuario = self.repo.get_by_id(db, usuario_id)
        if not usuario:
            raise NotFoundError("Usuario no encontrado")
        if current_user.rol != UserRole.ADMIN and current_user.id != usuario_id:
            raise ForbiddenError("No tienes permiso para ver este usuario")
        return usuario

    # ------------------------
    # LISTAR USUARIOS (Tu lógica original)
    # ------------------------
    def get_all(self, db: Session, skip: int = 0, limit: int = 100, actor_role: UserRole = None):
        if actor_role != UserRole.ADMIN:
            raise ForbiddenError("No tienes permisos para listar usuarios")
        return self.repo.get_all(db, skip=skip, limit=limit)

    # ------------------------
    # ACTUALIZAR USUARIO (Tu lógica original)
    # ------------------------
    def update(self, db: Session, usuario_id: int, payload: dict, current_user: Usuario) -> Usuario:
        usuario = self.repo.get_by_id(db, usuario_id)
        if not usuario:
            raise NotFoundError("Usuario no encontrado")

        if current_user.rol != UserRole.ADMIN and current_user.id != usuario_id:
            raise ForbiddenError("No puedes modificar este usuario")

        if "email" in payload:
            existing = self.repo.get_by_email(db, payload["email"])
            if existing and existing.id != usuario_id:
                raise BadRequestError("El email ya está en uso")

        if "password" in payload and payload["password"]:
            payload["password"] = get_password_hash(payload["password"])

        if "rol" in payload:
            if current_user.rol != UserRole.ADMIN:
                raise ForbiddenError("Solo ADMIN puede cambiar roles")
            if payload["rol"] == UserRole.ADMIN:
                raise ForbiddenError("No se puede asignar rol ADMIN")

        usuario = self.repo.update(db, usuario, payload)
        db.commit()
        return usuario

    # ------------------------
    # ELIMINAR USUARIO (Tu lógica original)
    # ------------------------
    def delete(self, db: Session, usuario_id: int, current_user: Usuario):
        usuario = self.repo.get_by_id(db, usuario_id)
        if not usuario:
            raise NotFoundError("Usuario no encontrado")

        if current_user.rol != UserRole.ADMIN:
            if current_user.id != usuario_id:
                raise ForbiddenError("No puedes eliminar otros usuarios")
            usuario = self.repo.update(db, usuario, {"activo": False})
            db.commit()
            return usuario

        deleted = self.repo.delete(db, usuario_id)
        db.commit()
        return deleted