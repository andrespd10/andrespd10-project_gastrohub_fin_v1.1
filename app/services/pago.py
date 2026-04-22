from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app.models import Pago
from app.models.enums import PedidoEstado
from app.repositories import PagoRepository, PedidoRepository
from app.services.exceptions import NotFoundError, BadRequestError


class PagoService:
    def __init__(self,
                 repository: PagoRepository = None,
                 pedido_repository: PedidoRepository = None):
        self.repo = repository or PagoRepository()
        self.pedido_repo = pedido_repository or PedidoRepository()

    def create(self, db: Session, payload: dict) -> Pago:
        pedido = self.pedido_repo.get_by_id(db, payload.get("pedido_id"))
        if not pedido:
            raise NotFoundError("Pedido no encontrado para pago")

        if pedido.estado == PedidoEstado.ABIERTO:
            raise BadRequestError("No se puede crear pago mientras el pedido está abierto")

        if pedido.pago:
            raise BadRequestError("El pedido ya tiene un pago registrado")

        total = sum(detalle.subtotal for detalle in pedido.detalles)

        if total <= 0:
            raise BadRequestError("El total del pago debe ser mayor que cero")

        pago_data = {
            "pedido_id": pedido.id,
            "total": total,
        }

        pago = self.repo.create(db, pago_data)
        db.commit()
        return pago

    def get_by_id(self, db: Session, pago_id: int) -> Pago:
        pago = self.repo.get_by_id(db, pago_id)
        if not pago:
            raise NotFoundError(f"Pago con id {pago_id} no encontrado")
        return pago

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return self.repo.get_all(db, skip=skip, limit=limit)

    def filter_by_date_range(
        self, db: Session, fecha_inicio: date, fecha_fin: date
    ) -> list[Pago]:
        if fecha_inicio > fecha_fin:
            raise BadRequestError(
                "La fecha de inicio no puede ser mayor que la fecha de fin"
            )
        inicio_dt = datetime.combine(fecha_inicio, time.min)
        fin_dt = datetime.combine(fecha_fin, time.max)
        return self.repo.filter_by_date_range(db, inicio_dt, fin_dt)