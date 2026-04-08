from sqlalchemy.orm import Session

from app.models import Producto
from app.repositories import ProductoRepository
from app.services.exceptions import NotFoundError, BadRequestError


class ProductoService:
    def __init__(self, repository: ProductoRepository = None):
        self.repo = repository or ProductoRepository()

    def create(self, db: Session, payload: dict) -> Producto:
        # Validar nombre único
        existing = db.query(Producto).filter(Producto.nombre == payload["nombre"]).first()
        if existing:
            raise BadRequestError("Ya existe un producto con ese nombre")

        # Validar precio
        if payload["precio"] <= 0:
            raise BadRequestError("El precio debe ser mayor que cero")

        producto = self.repo.create(db, payload)
        db.commit()
        return producto

    def get_by_id(self, db: Session, producto_id: int) -> Producto:
        producto = self.repo.get_by_id(db, producto_id)
        if not producto:
            raise NotFoundError(f"Producto con id {producto_id} no encontrado")
        return producto

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return self.repo.get_all(db, skip=skip, limit=limit)

    def update(self, db: Session, producto_id: int, payload: dict) -> Producto:
        producto = self.get_by_id(db, producto_id)

        # Validar nombre único
        if "nombre" in payload:
            existing = db.query(Producto).filter(Producto.nombre == payload["nombre"]).first()
            if existing and existing.id != producto_id:
                raise BadRequestError("Ya existe otro producto con ese nombre")

        # Validar precio
        if "precio" in payload and payload["precio"] is not None:
            if payload["precio"] <= 0:
                raise BadRequestError("El precio debe ser mayor que cero")

        producto = self.repo.update(db, producto, payload)
        db.commit()
        return producto

    def delete(self, db: Session, producto_id: int):
        producto = self.get_by_id(db, producto_id)

        # Validar si está en pedidos
        if producto.detalles:
            raise BadRequestError("No se puede eliminar un producto que tiene pedidos asociados")

        deleted = self.repo.delete(db, producto_id)
        db.commit()
        return deleted