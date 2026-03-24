from sqlalchemy.orm import Session

from app.models import Mesa
from app.repositories import MesaRepository
from app.services.exceptions import NotFoundError, BadRequestError


class MesaService:
    def __init__(self, repository: MesaRepository = None):
        self.repo = repository or MesaRepository()

    def create(self, db: Session, payload: dict) -> Mesa:
        # Validar número único
        existing = db.query(Mesa).filter(Mesa.numero == payload["numero"]).first()
        if existing:
            raise BadRequestError("Ya existe una mesa con ese número")

        mesa = self.repo.create(db, payload)
        db.commit()
        return mesa

    def get_by_id(self, db: Session, mesa_id: int) -> Mesa:
        mesa = self.repo.get_by_id(db, mesa_id)
        if not mesa:
            raise NotFoundError(f"Mesa con id {mesa_id} no encontrada")
        return mesa

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return self.repo.get_all(db, skip=skip, limit=limit)

    def update(self, db: Session, mesa_id: int, payload: dict) -> Mesa:
        mesa = self.get_by_id(db, mesa_id)

        if "numero" in payload:
            existing = db.query(Mesa).filter(Mesa.numero == payload["numero"]).first()
            if existing and existing.id != mesa_id:
                raise BadRequestError("Ya existe otra mesa con ese número")

        mesa = self.repo.update(db, mesa, payload)
        db.commit()
        return mesa

    def delete(self, db: Session, mesa_id: int):
        mesa = self.get_by_id(db, mesa_id)

        if mesa.pedidos:
            raise BadRequestError("No se puede eliminar una mesa con pedidos asociados")

        deleted = self.repo.delete(db, mesa_id)
        db.commit()
        return deleted