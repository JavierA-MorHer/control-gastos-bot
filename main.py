from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from api.webhook import router as webhook_router
from db.database import engine, Base, get_db
from db.models import Usuario

app = FastAPI(title="Control Gastos Bot")

# Registramos el router de webhook
app.include_router(webhook_router, prefix="/api")

@app.get("/")
async def ruta_principal(db: AsyncSession = Depends(get_db)):
    try:
        # Consultamos los primeros 5 usuarios para verificar la conexión
        query = select(Usuario).limit(5)
        resultado = await db.execute(query)
        usuarios = resultado.scalars().all()
        
        lista_usuarios = [{"id": u.id, "whatsapp": u.telefono_whatsapp, "nombre": u.nombre} for u in usuarios]
        
        return {
            "mensaje": "¡Conectado exitosamente a Neon DB!",
            "cantidad_usuarios": len(lista_usuarios),
            "usuarios_ejemplo": lista_usuarios
        }
    except Exception as e:
        return {"error_bd": str(e)}

@app.on_event("startup")
async def startup():
    # Creamos las tablas en Neon si no existen
    from db.models import Usuario, Gasto, Presupuesto
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)