from sqlalchemy.orm import Session

from app.models import Usuario
from app.repositories.base import BaseRepository


class UsuarioRepository(BaseRepository):
    def __init__(self):
        super().__init__(Usuario)

    def get_by_email(self, db: Session, email: str):
        return db.query(Usuario).filter(Usuario.email == email).first()
