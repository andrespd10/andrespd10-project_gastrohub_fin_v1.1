from app.models import Mesa
from app.repositories.base import BaseRepository


class MesaRepository(BaseRepository):
    def __init__(self):
        super().__init__(Mesa)
