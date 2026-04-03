import asyncio
from sqlalchemy import text
from db.database import engine

async def update_schema():
    async with engine.begin() as conn:
        try:
            # Intentamos añadir la columna, si ya existe soltará error, pero no pasa nada
            await conn.execute(text("ALTER TABLE usuarios ADD COLUMN estado_conversacion JSONB;"))
            print("Columna 'estado_conversacion' agregada a 'usuarios' exitosamente.")
        except Exception as e:
            print("Nota: La columna 'estado_conversacion' probablemente ya existe o hubo un error:", e)

if __name__ == "__main__":
    asyncio.run(update_schema())
