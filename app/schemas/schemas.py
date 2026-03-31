from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.enums import UserRole, MesaEstado, PedidoEstado, DetallePedidoEstado


# ------------------------
# TIPOS
# ------------------------
# Atención: Se usa Decimal con validaciones en los campos.


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
    nombre: str = Field(..., min_length=1, max_length=200)
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
    numero: int
    capacidad: int
    estado: MesaEstado = MesaEstado.LIBRE


class MesaCreate(MesaBase):
    pass


class MesaUpdate(BaseModel):
    numero: Optional[int] = None
    capacidad: Optional[int] = None
    estado: Optional[MesaEstado] = None


class MesaResponse(MesaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ------------------------
# PEDIDO
# ------------------------
class PedidoBase(BaseModel):
    mesa_id: int
    usuario_id: int
    estado: PedidoEstado = PedidoEstado.ABIERTO


class PedidoCreate(PedidoBase):
    pass


class PedidoUpdate(BaseModel):
    mesa_id: Optional[int] = None
    usuario_id: Optional[int] = None
    estado: Optional[PedidoEstado] = None


class PedidoResponse(PedidoBase):
    id: int
    fecha: datetime
    detalles: List["DetallePedidoResponse"] = Field(default_factory=list)
    pago: Optional["PagoResponse"] = None

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
    pedido_id: int
    producto_id: int
    cantidad: int


class DetallePedidoUpdate(BaseModel):
    cantidad: Optional[int] = None
    estado: Optional[DetallePedidoEstado] = None


class DetallePedidoResponse(BaseModel):
    id: int
    pedido_id: int
    producto_id: int
    cantidad: int
    precio_unitario: Decimal = Field(..., gt=0)
    subtotal: Decimal = Field(..., gt=0)
    estado: DetallePedidoEstado

    model_config = ConfigDict(from_attributes=True)


# ------------------------
# PAGO
# ------------------------
class PagoBase(BaseModel):
    pedido_id: int


class PagoCreate(PagoBase):
    pass


class PagoResponse(BaseModel):
    id: int
    pedido_id: int
    total: Decimal = Field(..., gt=0)
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------
# AUTH / RESET
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


class OTPRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


# Forward refs
PedidoResponse.model_rebuild()