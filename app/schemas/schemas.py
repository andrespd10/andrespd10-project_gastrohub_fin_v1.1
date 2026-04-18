from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.enums import UserRole, MesaEstado, PedidoEstado, DetallePedidoEstado

# ------------------------
# SCHEMAS DE REFERENCIA (Simples para anidar)
# ------------------------
class UsuarioSimple(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)

class ProductoSimple(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)

class MesaSimple(BaseModel):
    id: int
    numero: int
    model_config = ConfigDict(from_attributes=True)

# ------------------------
# USUARIO
# ------------------------
class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    rol: UserRole
    activo: bool = True

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8)

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    rol: Optional[UserRole] = None
    activo: Optional[bool] = None

class UsuarioResponse(UsuarioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ------------------------
# PRODUCTO
# ------------------------
class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    precio: Decimal = Field(..., gt=0)
    disponible: bool = True

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    precio: Optional[Decimal] = Field(None, gt=0)
    disponible: Optional[bool] = None

class ProductoResponse(ProductoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ------------------------
# MESA
# ------------------------
class MesaBase(BaseModel):
    numero: int = Field(..., gt=0) 
    capacidad: int = Field(..., gt=0) 
    estado: MesaEstado = MesaEstado.LIBRE

class MesaCreate(MesaBase):
    pass


class MesaResponse(MesaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ------------------------
# DETALLE PEDIDO
# ------------------------
class DetallePedidoBase(BaseModel):
    pedido_id: int
    producto_id: int
    cantidad: int
    estado: DetallePedidoEstado = DetallePedidoEstado.PENDIENTE

class DetallePedidoCreate(BaseModel):
    """Schema para crear un detalle de pedido (item/plato del pedido)"""
    producto_id: int
    cantidad: int = Field(..., gt=0)
    descripcion: Optional[str] = Field(None, max_length=500, description="Notas especiales: sin cebolla, extra picante, etc")

# Para enviar varios productos a un pedido en un solo JSON
class DetallePedidoBulkCreate(BaseModel):
    """Schema para agregar múltiples items a un pedido existente"""
    items: List[DetallePedidoCreate]

class DetallePedidoUpdate(BaseModel):
    """Schema para actualizar estado del item (SOLO COCINA)"""
    estado: DetallePedidoEstado

class DetallePedidoResponse(BaseModel):
    """Respuesta con detalles completos de un item del pedido"""
    id: int
    producto_id: int
    producto: Optional[ProductoSimple] = None 
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    descripcion: Optional[str] = None
    estado: DetallePedidoEstado
    model_config = ConfigDict(from_attributes=True)

# ------------------------
# PAGO
# ------------------------
class PagoResponse(BaseModel):
    id: int
    pedido_id: int
    total: Decimal
    fecha: datetime
    model_config = ConfigDict(from_attributes=True)

# ------------------------
# PEDIDO
# ------------------------
class PedidoBase(BaseModel):
    mesa_id: int
    usuario_id: int
    estado: PedidoEstado = PedidoEstado.ABIERTO

class PedidoCreate(BaseModel):
    """Schema para crear un pedido completo con mesa e items en una sola acción"""
    mesa_id: int
    items: List[DetallePedidoCreate] = Field(..., min_length=1, description="Al menos un producto es requerido")

class PedidoUpdateItem(BaseModel):
    """Schema para actualizar/editar un item dentro de un pedido"""
    detalle_id: int = Field(..., description="ID del item/plato a modificar")
    cantidad: Optional[int] = Field(None, gt=0, description="Nueva cantidad. Si es 0, el item será eliminado")
    descripcion: Optional[str] = Field(None, max_length=500, description="Actualizar notas especiales")

class PedidoUpdateItems(BaseModel):
    """Schema para actualizar múltiples items de un pedido a la vez"""
    items: List[PedidoUpdateItem] = Field(..., min_length=1)

class PedidoUpdate(BaseModel):
    """Schema para actualizar estado general del pedido"""
    estado: Optional[PedidoEstado] = None

class PedidoResponse(BaseModel):
    id: int
    fecha: datetime
    estado: PedidoEstado
    mesa_id: int
    usuario_id: int
    mesa: Optional[MesaSimple] = None
    usuario: Optional[UsuarioSimple] = None
    detalles: List[DetallePedidoResponse] = Field(default_factory=list)
    pago: Optional[PagoResponse] = None

    model_config = ConfigDict(from_attributes=True)

# ------------------------
# AUTH / TOKEN
# ------------------------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[UserRole] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    recaptcha_token: str = Field(..., min_length=10)

# Reconstruir para manejar referencias circulares de detalles
PedidoResponse.model_rebuild()

# ------------------------
# AUTH / RESET 
# ------------------------
class OTPRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)