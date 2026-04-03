"""
Punto de entrada de la aplicación FastAPI.
Responsabilidad: crear la app, registrar routers y manejar el startup de la DB.
"""
from fastapi import FastAPI
from api.webhook import router as webhook_router
from db.database import engine, Base

app = FastAPI(title="Control Gastos Bot")

# Registrar routers
app.include_router(webhook_router, prefix="/api")


@app.get("/")
async def health_check():
    """Ruta de verificación de salud del servidor."""
    return {"status": "ok", "mensaje": "Control Gastos Bot está en línea 🚀"}


@app.on_event("startup")
async def startup():
    """Crea las tablas en Neon DB si no existen."""
    # Importamos todos los modelos para que SQLAlchemy los registre
    from db.models import Usuario, Gasto, Presupuesto, CategoriaUsuario  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)