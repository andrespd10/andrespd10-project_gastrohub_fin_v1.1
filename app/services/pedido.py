from sqlalchemy.orm import Session
from decimal import Decimal

from app.models import Pedido, DetallePedido, Pago, Mesa
from app.models.enums import PedidoEstado, DetallePedidoEstado, MesaEstado
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
    # LECTURA (LISTAR)
    # ------------------------

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return self.pedido_repo.get_all(db, skip=skip, limit=limit)

    def get_pedidos_cocina(self, db: Session):
        """Pedidos en orden de llegada para cocina"""
        return self.pedido_repo.get_pedidos_pendientes_cocina(db)

    def get_pedidos_by_usuario(self, db: Session, usuario_id: int):
        """Pedidos de un mesero"""
        return self.pedido_repo.get_by_usuario(db, usuario_id)

    def get_by_id(self, db: Session, pedido_id: int) -> Pedido:
        pedido = self.pedido_repo.get_by_id(db, pedido_id)
        if not pedido:
            raise NotFoundError(f"Pedido con id {pedido_id} no encontrado")
        return pedido

    # ------------------------
    # CREATE
    # ------------------------

    def create(self, db: Session, mesa_id: int, current_user_id: int) -> Pedido:
        mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()

        if not mesa:
            raise NotFoundError("Mesa no encontrada")

        if mesa.estado == MesaEstado.OCUPADA:
            raise BadRequestError("La mesa ya está ocupada")

        pedido = self.pedido_repo.create(db, {
            "mesa_id": mesa_id,
            "usuario_id": current_user_id,
            "estado": PedidoEstado.ABIERTO
        })

        # 🔥 Mesa pasa a ocupada
        mesa.estado = MesaEstado.OCUPADA

        db.commit()
        return pedido

    # ------------------------
    # UPDATE
    # ------------------------

    def update(self, db: Session, pedido_id: int, payload: dict) -> Pedido:
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("No se puede modificar un pedido ya cerrado")

        # 🔥 VALIDACIÓN CLAVE: no cerrar sin productos
        if payload.get("estado") == PedidoEstado.CERRADO:
            if not pedido.detalles:
                raise BadRequestError("No se puede cerrar un pedido sin productos")

            # 🔥 liberar mesa al cerrar
            pedido.mesa.estado = MesaEstado.LIBRE

        updated = self.pedido_repo.update(db, pedido, payload)
        db.commit()
        return updated

    # ------------------------
    # DELETE
    # ------------------------

    def delete(self, db: Session, pedido_id: int):
        pedido = self.get_by_id(db, pedido_id)

        # 🔥 NO permitir eliminar pedidos cerrados
        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("No se puede eliminar un pedido cerrado")

        # 🔥 liberar mesa si estaba abierto
        if pedido.estado == PedidoEstado.ABIERTO:
            pedido.mesa.estado = MesaEstado.LIBRE

        deleted = self.pedido_repo.delete(db, pedido_id)
        db.commit()
        return deleted

    # ------------------------
    # DETALLE PEDIDO
    # ------------------------

    def add_detalle(self, db: Session, pedido_id: int, producto_id: int, cantidad: int) -> DetallePedido:
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("No se puede agregar productos a un pedido cerrado")

        producto = self.producto_repo.get_by_id(db, producto_id)

        if not producto or not producto.disponible:
            raise BadRequestError("Producto no disponible")

        subtotal = producto.precio * cantidad

        detalle = self.detalle_repo.create(db, {
            "pedido_id": pedido_id,
            "producto_id": producto_id,
            "cantidad": cantidad,
            "precio_unitario": producto.precio,
            "subtotal": subtotal,
            "estado": DetallePedidoEstado.PENDIENTE
        })

        db.commit()
        return detalle

    # ------------------------
    # CERRAR PEDIDO (OPCIONAL)
    # ------------------------

    def cerrar_pedido(self, db: Session, pedido_id: int) -> Pedido:
        """
        Este método es opcional si usas update,
        pero lo dejamos por buenas prácticas.
        """
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("El pedido ya está cerrado")

        if not pedido.detalles:
            raise BadRequestError("No se puede cerrar un pedido vacío")

        pedido.estado = PedidoEstado.CERRADO
        pedido.mesa.estado = MesaEstado.LIBRE

        db.commit()
        return pedido

    # ------------------------
    # PAGO
    # ------------------------

    def create_pago(self, db: Session, pedido_id: int) -> Pago:
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.ABIERTO:
            raise BadRequestError("Debe cerrar el pedido antes de pagar")

        if pedido.pago:
            raise BadRequestError("El pedido ya tiene un pago registrado")

        if not pedido.detalles:
            raise BadRequestError("No se puede pagar un pedido vacío")

        total = sum(d.subtotal for d in pedido.detalles)

        pago = self.pago_repo.create(db, {
            "pedido_id": pedido_id,
            "total": total
        })

        db.commit()
        return pago