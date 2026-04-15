from sqlalchemy.orm import Session
from decimal import Decimal
from app.models.enums import DetallePedidoEstado

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
    # CREATE - Crear pedido completo con mesa e items en una acción
    # ------------------------

    def create(self, db: Session, mesa_id: int, current_user_id: int, items: list) -> Pedido:
        """
        Crea un pedido con mesa y todos sus productos de una sola vez.
        
        Args:
            db: Sesión de base de datos
            mesa_id: ID de la mesa
            current_user_id: ID del mesero que crea el pedido
            items: Lista de items (DetallePedidoCreate) con producto_id, cantidad, descripcion
        
        Returns:
            Pedido creado con todos sus detalles
        """
        # Validar mesa
        mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
        if not mesa:
            raise NotFoundError("Mesa no encontrada")

        if mesa.estado == MesaEstado.OCUPADA:
            raise BadRequestError("La mesa ya está ocupada")

        if not items or len(items) == 0:
            raise BadRequestError("Debe agregar al menos un producto al pedido")

        # Crear pedido
        pedido = self.pedido_repo.create(db, {
            "mesa_id": mesa_id,
            "usuario_id": current_user_id,
            "estado": PedidoEstado.ABIERTO
        })

        # Crear todos los detalles
        for item in items:
            producto = self.producto_repo.get_by_id(db, item.producto_id)
            
            if not producto or not producto.disponible:
                db.rollback()
                raise BadRequestError(f"Producto ID {item.producto_id} no disponible o no existe")

            subtotal = producto.precio * item.cantidad

            self.detalle_repo.create(db, {
                "pedido_id": pedido.id,
                "producto_id": item.producto_id,
                "cantidad": item.cantidad,
                "precio_unitario": producto.precio,
                "subtotal": subtotal,
                "descripcion": item.descripcion,
                "estado": DetallePedidoEstado.PENDIENTE
            })

        # Marcar mesa como ocupada
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

    def update_items(self, db: Session, pedido_id: int, items_to_update: list) -> dict:
        """
        Actualiza múltiples items de un pedido.
        Se pueden cambiar cantidades, descripciones o eliminar items.
        
        Args:
            db: Sesión de base de datos
            pedido_id: ID del pedido
            items_to_update: Lista de {detalle_id, cantidad (opcional), descripcion (opcional)}
                            Si cantidad es 0 o None, el item se elimina
        
        Returns:
            Diccionario con resumen de cambios
        """
        pedido = self.get_by_id(db, pedido_id)

        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("No se puede editar un pedido ya cerrado")

        if not items_to_update or len(items_to_update) == 0:
            raise BadRequestError("Debe proporcionar items a actualizar")

        cambios = {"actualizados": [], "eliminados": []}

        for item in items_to_update:
            detalle = self.detalle_repo.get_by_id(db, item.detalle_id)
            
            if not detalle or detalle.pedido_id != pedido_id:
                raise NotFoundError(f"Detalle {item.detalle_id} no pertenece a este pedido")

            # Si cantidad es 0 o None, eliminar el item
            if item.cantidad is None or item.cantidad == 0:
                self.detalle_repo.delete(db, item.detalle_id)
                cambios["eliminados"].append(item.detalle_id)
            else:
                # Actualizar cantidad y descripción si es necesario
                update_data = {"cantidad": item.cantidad}
                
                if item.descripcion is not None:
                    update_data["descripcion"] = item.descripcion
                
                # Recalcular subtotal
                update_data["subtotal"] = detalle.precio_unitario * item.cantidad
                
                self.detalle_repo.update(db, detalle, update_data)
                cambios["actualizados"].append(item.detalle_id)

        # Validar que el pedido no quede sin productos
        if len(pedido.detalles) - len(cambios["eliminados"]) == 0:
            db.rollback()
            raise BadRequestError("No se puede dejar un pedido sin productos")

        db.commit()
        return cambios

    # ------------------------
    # DELETE
    # ------------------------
    def delete(self, db: Session, pedido_id: int):
        pedido = self.get_by_id(db, pedido_id)

        # 1. NO permitir eliminar pedidos ya cerrados
        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("No se puede eliminar un pedido que ya está CERRADO.")

        # 2. VALIDACIÓN SOLICITADA: Bloqueo por avance en cocina
        for detalle in pedido.detalles:
            # Si el estado es PREPARANDO o LISTO, lanzamos el mensaje exacto
            if detalle.estado in [DetallePedidoEstado.PREPARANDO, DetallePedidoEstado.LISTO]:
                raise BadRequestError("No se puede eliminar un pedido que ya tiene productos en preparación o listos")

        # 3. Liberar la mesa antes de borrar el registro
        if pedido.mesa:
            pedido.mesa.estado = MesaEstado.LIBRE

        # Guardamos el ID para el mensaje de confirmación
        mesa_id = pedido.mesa_id
        
        # 4. Ejecutamos la eliminación física en la base de datos
        self.pedido_repo.delete(db, pedido_id)
        db.commit()
        
        return f"Pedido {pedido_id} eliminado exitosamente y mesa {mesa_id} liberada"
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
        # 1. Obtener el pedido por ID
        pedido = self.get_by_id(db, pedido_id)

        # 2. Validar que el pedido no esté ya cerrado
        if pedido.estado == PedidoEstado.CERRADO:
            raise BadRequestError("El pedido ya está cerrado")

        # 3. Validar que el pedido tenga productos
        if not pedido.detalles:
            raise BadRequestError("No se puede cerrar un pedido vacío")

        # 4. --- VALIDACIÓN DE INTEGRIDAD DE PRODUCTOS ---
        # Recorremos cada producto del pedido para asegurar que la cocina terminó
        for detalle in pedido.detalles:
            # Si algún producto NO está en estado LISTO, lanzamos error
            if detalle.estado != DetallePedidoEstado.LISTO:
                raise BadRequestError(
                    f"No se puede cerrar. El producto '{detalle.producto.nombre}' "
                    f"aún está en estado: {detalle.estado.value}"
                )
        # ------------------------------------------------

        # 5. Cambiar el estado del pedido a CERRADO
        pedido.estado = PedidoEstado.CERRADO
        
        # 6. Liberar la mesa asociada (si existe)
        if pedido.mesa:
            pedido.mesa.estado = MesaEstado.LIBRE

        # 7. Guardar cambios en la base de datos
        db.commit()
        db.refresh(pedido)
        
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