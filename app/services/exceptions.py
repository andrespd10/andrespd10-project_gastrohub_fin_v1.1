class ServiceError(Exception):
    pass


class NotFoundError(ServiceError):
    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message)


class BadRequestError(ServiceError):
    def __init__(self, message: str = "Solicitud inválida"):
        super().__init__(message)


class ForbiddenError(ServiceError):
    def __init__(self, message: str = "Acceso denegado"):
        super().__init__(message)
