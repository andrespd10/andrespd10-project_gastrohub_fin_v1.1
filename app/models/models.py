from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta

BOGOTA_TZ = timezone(timedelta(hours=-5))  # America/Bogota (UTC-5, sin horario de verano)

from app.db.base import Base
from app.models.enums import UserRole, MesaEstado, PedidoEstado, DetallePedidoEstado

# =========================
# USUARIO
# =========================
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    rol = Column(Enum(UserRole), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    # Relación con Pedido
    pedidos = relationship("Pedido", back_populates="usuario")


# =========================
# PRODUCTO
# =========================
class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(String(500), nullable=True)
    precio = Column(Numeric(10, 2), nullable=False)
    disponible = Column(Boolean, default=True, nullable=False)

    # Relación con DetallePedido
    detalles = relationship("DetallePedido", back_populates="producto")


# =========================
# MESA
# =========================
class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    numero = Column(Integer, unique=True, nullable=False)
    capacidad = Column(Integer, nullable=False)
    estado = Column(Enum(MesaEstado), default=MesaEstado.LIBRE, nullable=False)

    # Relación con Pedido
    pedidos = relationship("Pedido", back_populates="mesa")


# =========================
# PEDIDO
# =========================
class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mesa_id = Column(Integer, ForeignKey("mesas.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha = Column(DateTime, default=lambda: datetime.now(BOGOTA_TZ), nullable=False)
    estado = Column(Enum(PedidoEstado), default=PedidoEstado.ABIERTO, nullable=False)

    # Relaciones - Estos nombres deben coincidir con PedidoResponse en schemas.py
    mesa = relationship("Mesa", back_populates="pedidos")
    usuario = relationship("Usuario", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")
    pago = relationship("Pago", back_populates="pedido", uselist=False, cascade="all, delete-orphan")


# =========================
# DETALLE PEDIDO
# =========================
class DetallePedido(Base):
    __tablename__ = "detalle_pedidos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False, index=True)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    descripcion = Column(String(500), nullable=True)
    estado = Column(Enum(DetallePedidoEstado), default=DetallePedidoEstado.PENDIENTE, nullable=False)

    # Relaciones
    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles")

    @property
    def numero_mesa(self) -> int | None:
        """Devuelve el número de mesa a través de la relación pedido → mesa."""
        if self.pedido and self.pedido.mesa:
            return self.pedido.mesa.numero
        return None


# =========================
# PAGO
# =========================
class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total = Column(Numeric(10, 2), nullable=False)
    fecha = Column(DateTime, default=lambda: datetime.now(BOGOTA_TZ), nullable=False)

    # Relación
    pedido = relationship("Pedido", back_populates="pago")