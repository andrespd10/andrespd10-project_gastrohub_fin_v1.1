from sqlalchemy.orm import Session

from app.models import DetallePedido
from app.repositories import DetallePedidoRepository
from app.services.exceptions import NotFoundError, BadRequestError


class DetallePedidoService:
    def __init__(self, repository: DetallePedidoRepository = None):
        self.repo = repository or DetallePedidoRepository()

    def get_by_id(self, db: Session, detalle_id: int) -> DetallePedido:
        detalle = self.repo.get_by_id(db, detalle_id)
        if not detalle:
            raise NotFoundError(f"DetallePedido con id {detalle_id} no encontrado")
        return detalle

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return self.repo.get_all(db, skip=skip, limit=limit)

    def update(self, db: Session, detalle_id: int, payload: dict) -> DetallePedido:
        detalle = self.get_by_id(db, detalle_id)
        if detalle.pedido.estado == "CERRADO":
            raise BadRequestError("No se puede modificar el detalle de un pedido cerrado")

        if "cantidad" in payload and payload["cantidad"] is not None:
            cantidad = payload["cantidad"]
            detalle.subtotal = detalle.precio_unitario * cantidad

        detalle = self.repo.update(db, detalle, payload)
        db.commit()
        return detalle

    def delete(self, db: Session, detalle_id: int) -> DetallePedido:
        detalle = self.get_by_id(db, detalle_id)
        if detalle.pedido.estado == "CERRADO":
            raise BadRequestError("No se puede eliminar el detalle de un pedido cerrado")

        deleted = self.repo.delete(db, detalle_id)
        if not deleted:
            raise NotFoundError(f"DetallePedido con id {detalle_id} no encontrado")
        db.commit()
        return deleted
