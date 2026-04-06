from sqlalchemy.orm import Session
from app.models import Usuario
from app.repositories.base import BaseRepository

class UsuarioRepository(BaseRepository):
    def __init__(self):
        # Inicializa el repositorio base con el modelo Usuario
        super().__init__(Usuario)

    def get_by_email(self, db: Session, email: str):
        """
        Busca un usuario en la base de datos por su dirección de correo.
        """
        return db.query(Usuario).filter(Usuario.email == email).first()