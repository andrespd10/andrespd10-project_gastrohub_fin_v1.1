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

        # Mesa pasa a ocupada
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

        # VALIDACIÓN CLAVE: no cerrar sin productos
        if payload.get("estado") == PedidoEstado.CERRADO:
            if not pedido.detalles:
                raise BadRequestError("No se puede cerrar un pedido sin productos")

            # liberar mesa al cerrar
            pedido.mesa.estado = MesaEstado.LIBRE

        updated = self.pedido_repo.update(db, pedido, payload)
        db.commit()
        return updated

    # ------------------------
    # DELETE
    # ------------------------
    def delete(self, db: Session, pedido_id: int):
            pedido = self.get_by_id(db, pedido_id)

            # NO permitir eliminar pedidos cerrados
            if pedido.estado == PedidoEstado.CERRADO:
                raise BadRequestError("No se puede eliminar un pedido cerrado")

            # liberar mesa si estaba abierto
            if pedido.estado == PedidoEstado.ABIERTO:
                pedido.mesa.estado = MesaEstado.LIBRE

            # Ejecutamos la eliminación
            self.pedido_repo.delete(db, pedido_id)
            db.commit()
            
            # CAMBIO CLAVE: No retornamos 'deleted'. 
            # Simplemente retornamos True o nada.
            return f"Pedido {pedido_id} eliminado exitosamente y mesa {pedido.mesa_id} liberada"

    # ------------------------
    # DETALLE PEDIDO (Individual y Masivo)
    # ------------------------

    def add_detalle(self, db: Session, pedido_id: int, producto_id: int, cantidad: int) -> DetallePedido:
        """Agrega un solo producto (mantenido por compatibilidad)"""
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("No se puede agregar productos a un pedido cerrado")

        producto = self.producto_repo.get_by_id(db, producto_id)

        if not producto or not producto.disponible:
            raise BadRequestError(f"Producto ID {producto_id} no disponible o no existe")

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

    # MÉTODO ACTUALIZADO: AGREGAR VARIOS PRODUCTOS CON ID DE USUARIO
    def add_multiple_detalles(self, db: Session, pedido_id: int, items: list, usuario_id: int) -> dict:
        """
        Recorre una lista de productos y los agrega todos al mismo pedido.
        Recibe usuario_id para validar quién hace la operación.
        """
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("No se pueden agregar productos a un pedido cerrado")

        # Registro de auditoría simple (esto quita el aviso en el router)
        print(f"INFO: El usuario ID {usuario_id} está agregando productos al pedido {pedido_id}")

        detalles_creados = []

        for item in items:
            producto = self.producto_repo.get_by_id(db, item.producto_id)
            
            if not producto or not producto.disponible:
                db.rollback() 
                raise BadRequestError(f"Producto ID {item.producto_id} no existe o no está disponible")

            subtotal = producto.precio * item.cantidad

            nuevo_detalle = self.detalle_repo.create(db, {
                "pedido_id": pedido_id,
                "producto_id": item.producto_id,
                "cantidad": item.cantidad,
                "precio_unitario": producto.precio,
                "subtotal": subtotal,
                "estado": DetallePedidoEstado.PENDIENTE
            })
            detalles_creados.append(nuevo_detalle)

        db.commit()
        return {"message": f"Usuario {usuario_id} agregó {len(detalles_creados)} productos al pedido {pedido_id}"}

    # ------------------------
    # CERRAR PEDIDO
    # ------------------------

    def cerrar_pedido(self, db: Session, pedido_id: int) -> Pedido:
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

        total = self.calculate_pago_total(db, pedido_id)

        pago = self.pago_repo.create(db, {
            "pedido_id": pedido_id,
            "total": total
        })

        db.commit()
        return pago

    def calculate_pago_total(self, db: Session, pedido_id: int) -> Decimal:
        pedido = self.get_by_id(db, pedido_id)
        return sum(d.subtotal for d in pedido.detalles)