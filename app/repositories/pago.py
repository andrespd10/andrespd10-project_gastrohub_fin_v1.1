from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Pago
from app.repositories.base import BaseRepository


class PagoRepository(BaseRepository):
    def __init__(self):
        super().__init__(Pago)

    def filter_by_date_range(
        self, db: Session, fecha_inicio: datetime, fecha_fin: datetime
    ) -> list[Pago]:
        return (
            db.query(Pago)
            .filter(Pago.fecha >= fecha_inicio, Pago.fecha <= fecha_fin)
            .order_by(Pago.fecha.desc())
            .all()
        )
