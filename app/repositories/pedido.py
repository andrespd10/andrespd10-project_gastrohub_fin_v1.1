from sqlalchemy.orm import Session, joinedload
from app.models import Pedido, DetallePedido
from app.models.enums import DetallePedidoEstado, PedidoEstado
from app.repositories.base import BaseRepository

class PedidoRepository(BaseRepository):
    def __init__(self):
        super().__init__(Pedido)

    def get_by_id(self, db: Session, pedido_id: int):
        return db.query(Pedido).options(
            joinedload(Pedido.mesa),
            joinedload(Pedido.usuario),
            joinedload(Pedido.pago),
            joinedload(Pedido.detalles).joinedload(DetallePedido.producto)
        ).filter(Pedido.id == pedido_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(Pedido).options(
            joinedload(Pedido.mesa),
            joinedload(Pedido.usuario)
        ).order_by(Pedido.fecha_creacion.desc()).offset(skip).limit(limit).all()

    def get_by_usuario(self, db: Session, usuario_id: int):
        """Filtra pedidos creados por el mesero actual"""
        return db.query(Pedido).options(
            joinedload(Pedido.mesa),
            joinedload(Pedido.usuario)
        ).filter(Pedido.usuario_id == usuario_id).all()

    def get_pedidos_pendientes_cocina(self, db: Session):
        """Filtra pedidos que tengan platos pendientes o en preparación"""
        return db.query(Pedido).join(DetallePedido).options(
            joinedload(Pedido.mesa),
            joinedload(Pedido.usuario),
            joinedload(Pedido.detalles).joinedload(DetallePedido.producto)
        ).filter(
            DetallePedido.estado.in_([DetallePedidoEstado.PENDIENTE, DetallePedidoEstado.PREPARANDO])
        ).distinct().all()