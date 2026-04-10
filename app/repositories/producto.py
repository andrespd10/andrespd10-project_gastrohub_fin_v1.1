from app.models import Producto
from app.repositories.base import BaseRepository


class ProductoRepository(BaseRepository):
    def __init__(self):
        super().__init__(Producto)
