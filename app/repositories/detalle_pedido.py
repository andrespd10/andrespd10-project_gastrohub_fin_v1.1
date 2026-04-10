from sqlalchemy.orm import Session
from typing import List
from app.models import DetallePedido
from app.repositories.base import BaseRepository

class DetallePedidoRepository(BaseRepository):
    def __init__(self):
        super().__init__(DetallePedido)

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[DetallePedido]:
        """
        FILTRO DE COCINA: Retorna solo los platos que el cocinero debe preparar.
        Los platos en estado 'LISTO', 'ENTREGADO' o de pedidos 'CERRADOS' 
        no aparecen aquí.
        """
        return db.query(self.model).filter(
            self.model.estado.in_(["PENDIENTE", "PREPARANDO"])
        ).offset(skip).limit(limit).all()