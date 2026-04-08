import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MESERO = "MESERO"
    COCINA = "COCINA"


class MesaEstado(str, enum.Enum):
    LIBRE = "LIBRE"
    OCUPADA = "OCUPADA"


class PedidoEstado(str, enum.Enum):
    ABIERTO = "ABIERTO"
    CERRADO = "CERRADO"


class DetallePedidoEstado(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    PREPARANDO = "PREPARANDO"
    LISTO = "LISTO"
