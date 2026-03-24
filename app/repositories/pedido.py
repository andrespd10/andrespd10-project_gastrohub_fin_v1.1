from app.models import Pedido
from app.repositories.base import BaseRepository


class PedidoRepository(BaseRepository):
    def __init__(self):
        super().__init__(Pedido)
