from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import time

from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.routes.usuarios import router as usuarios_router
from app.api.routes.productos import router as productos_router
from app.api.routes.mesas import router as mesas_router
from app.api.routes.pedidos import router as pedidos_router
from app.api.routes.detalle_pedido import router as detalles_pedido_router
from app.api.routes.pagos import router as pagos_router

from app.db.base import Base
from app.db.session import engine
import app.models.models as models

# Creación de tablas en MySQL
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GastroHub API", version="1.0.0")

# CORS configurado desde settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_hosts(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenamiento temporal en memoria para los límites
_limit_store = {}
def rate_limiter(client_ip: str, path: str, method: str):
    now = datetime.now()
    window_start = now - timedelta(seconds=60)
    key = f"{client_ip}:{path}"
    
    hits = _limit_store.get(key, [])
    hits = [h for h in hits if h > window_start]
    hits.append(now)
    _limit_store[key] = hits

    # --- LÓGICA DE LÍMITES ESPECÍFICOS ---
    
    # 1. Login (Muy estricto: 3)
    if "/auth/login" in path:
        limit = settings.RATE_LIMIT_LOGIN

    # 2. Creación de Usuarios (Estricto: 5 por minuto para evitar spam)
    elif "/usuarios" in path and method == "POST":
        limit = 5

    # 3. Recuperación de Contraseña (Muy estricto: 2 por minuto)
    elif "/auth/reset-password" in path:
        limit = 2

    # 4. Pagos (Crítico: 5 por minuto para evitar cobros duplicados)
    elif "/pagos" in path and method == "POST":
        limit = 10

    # 5. Límite General para todo lo demás (Mesas, Productos, Ver Pedidos)
    else:
        limit = settings.RATE_LIMIT_PER_MINUTE
    
    if len(hits) > limit:
        return False
    return True

@app.middleware("http")
async def limit_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    method = request.method  # <--- Agregamos esta línea para obtener el método (POST, GET, etc.)

    # Ejecutar validación de tasa
    if not rate_limiter(client_ip, path, method):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Demasiados intentos. Límite de {settings.RATE_LIMIT_LOGIN} peticiones por minuto para esta ruta.",
                "type": "rate_limit_exceeded"
            },
        )

    # Medición de tiempo de respuesta (X-Process-Time)
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor", "message": str(exc)},
    )

# Inclusión de Routers
app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(productos_router)
app.include_router(mesas_router)
app.include_router(pedidos_router)
app.include_router(detalles_pedido_router)
app.include_router(pagos_router)