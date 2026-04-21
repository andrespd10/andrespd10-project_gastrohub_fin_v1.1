from sqlalchemy.orm import Session
from typing import List
from app.models import DetallePedido, Pedido
from app.repositories.base import BaseRepository

class DetallePedidoRepository(BaseRepository):
    def __init__(self):
        super().__init__(DetallePedido)

    def get_by_pedido(self, db: Session, pedido_id: int) -> List[DetallePedido]:
        """
        Retorna todos los detalles (productos) que pertenecen a un pedido específico,
        ordenados por id ascendente.
        """
        return (
            db.query(self.model)
            .join(Pedido, self.model.pedido_id == Pedido.id)
            .filter(self.model.pedido_id == pedido_id)
            .order_by(self.model.id.asc())
            .all()
        )

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[DetallePedido]:
        """
        FILTRO DE COCINA: Retorna solo los platos que el cocinero debe preparar.
        Los platos en estado 'LISTO', 'ENTREGADO' o de pedidos 'CERRADOS' 
        no aparecen aquí. Ordenados por fecha de creación del pedido (más antiguo primero).
        """
        return (
            db.query(self.model)
            .join(Pedido, self.model.pedido_id == Pedido.id)
            .filter(self.model.estado.in_(["PENDIENTE", "PREPARANDO"]))
            .order_by(Pedido.fecha.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )