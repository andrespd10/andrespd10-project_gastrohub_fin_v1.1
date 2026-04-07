from app.models import Pago
from app.repositories.base import BaseRepository


class PagoRepository(BaseRepository):
    def __init__(self):
        super().__init__(Pago)
