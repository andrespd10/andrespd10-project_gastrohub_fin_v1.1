from app.models import DetallePedido
from app.repositories.base import BaseRepository


class DetallePedidoRepository(BaseRepository):
    def __init__(self):
        super().__init__(DetallePedido)
