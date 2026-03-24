from sqlalchemy.orm import Session

from app.models import Pedido, DetallePedido, Pago
from app.models.enums import PedidoEstado, DetallePedidoEstado
from app.repositories import (
    PedidoRepository,
    DetallePedidoRepository,
    PagoRepository,
    ProductoRepository,
)
from app.services.exceptions import NotFoundError, BadRequestError


class PedidoService:
    def __init__(self,
                 pedido_repo: PedidoRepository = None,
                 detalle_repo: DetallePedidoRepository = None,
                 pago_repo: PagoRepository = None,
                 producto_repo: ProductoRepository = None):
        self.pedido_repo = pedido_repo or PedidoRepository()
        self.detalle_repo = detalle_repo or DetallePedidoRepository()
        self.pago_repo = pago_repo or PagoRepository()
        self.producto_repo = producto_repo or ProductoRepository()

    # ------------------------
    # PEDIDO
    # ------------------------

    def create(self, db: Session, payload: dict) -> Pedido:
        if payload.get("estado") not in (None, PedidoEstado.ABIERTO):
            raise BadRequestError("No es posible crear un pedido con estado distinto de ABIERTO")

        pedido = self.pedido_repo.create(db, payload)
        db.commit()
        return pedido

    def get_by_id(self, db: Session, pedido_id: int) -> Pedido:
        pedido = self.pedido_repo.get_by_id(db, pedido_id)
        if not pedido:
            raise NotFoundError(f"Pedido con id {pedido_id} no encontrado")
        return pedido

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return self.pedido_repo.get_all(db, skip=skip, limit=limit)

    def update(self, db: Session, pedido_id: int, payload: dict) -> Pedido:
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("No se puede modificar un pedido cerrado")

        updated = self.pedido_repo.update(db, pedido, payload)
        db.commit()
        return updated

    def delete(self, db: Session, pedido_id: int):
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("No se puede eliminar un pedido cerrado")

        deleted = self.pedido_repo.delete(db, pedido_id)
        if not deleted:
            raise NotFoundError(f"Pedido con id {pedido_id} no encontrado")

        db.commit()
        return deleted

    # ------------------------
    # DETALLE PEDIDO
    # ------------------------

    def add_detalle(self, db: Session, pedido_id: int, payload: dict) -> DetallePedido:
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("No se puede añadir detalle a un pedido cerrado")

        producto = self.producto_repo.get_by_id(db, payload["producto_id"])
        if not producto:
            raise NotFoundError("Producto no encontrado")

        precio_unitario = producto.precio
        cantidad = payload.get("cantidad", 1)
        subtotal = precio_unitario * cantidad

        detalle_data = {
            "pedido_id": pedido_id,
            "producto_id": producto.id,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "subtotal": subtotal,
            "estado": payload.get("estado", DetallePedidoEstado.PENDIENTE),
        }

        detalle = self.detalle_repo.create(db, detalle_data)
        db.commit()
        return detalle

    def update_detalle(self, db: Session, detalle_id: int, payload: dict) -> DetallePedido:
        detalle = self.detalle_repo.get_by_id(db, detalle_id)

        if not detalle:
            raise NotFoundError(f"DetallePedido con id {detalle_id} no encontrado")

        if detalle.pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("No se puede modificar detalle de un pedido cerrado")

        update_data = {}

        if "cantidad" in payload and payload["cantidad"] is not None:
            cantidad = payload["cantidad"]
            update_data["cantidad"] = cantidad
            update_data["subtotal"] = detalle.precio_unitario * cantidad

        if "estado" in payload and payload["estado"] is not None:
            update_data["estado"] = payload["estado"]

        detalle = self.detalle_repo.update(db, detalle, update_data)
        db.commit()
        return detalle

    # ------------------------
    # LÓGICA DE PEDIDO
    # ------------------------

    def cerrar_pedido(self, db: Session, pedido_id: int) -> Pedido:
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("El pedido ya está cerrado")

        if not pedido.detalles:
            raise BadRequestError("No se puede cerrar un pedido sin productos")

        pedido = self.pedido_repo.update(
            db,
            pedido,
            {"estado": PedidoEstado.CERRADO}
        )

        db.commit()
        return pedido

    def calculate_pago_total(self, db: Session, pedido_id: int) -> float:
        pedido = self.get_by_id(db, pedido_id)
        total = sum(detalle.subtotal for detalle in pedido.detalles)
        return float(total)

    def create_pago(self, db: Session, pedido_id: int) -> Pago:
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.ABIERTO:
            raise BadRequestError("Debe cerrar el pedido antes de generar el pago")

        if pedido.pago:
            raise BadRequestError("El pedido ya tiene un pago registrado")

        if not pedido.detalles:
            raise BadRequestError("No se puede crear pago para pedido sin detalles")

        total = sum(detalle.subtotal for detalle in pedido.detalles)

        pago_data = {
            "pedido_id": pedido_id,
            "total": total,
        }

        pago = self.pago_repo.create(db, pago_data)
        db.commit()
        return pago