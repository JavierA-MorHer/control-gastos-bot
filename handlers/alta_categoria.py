"""Handler: Alta de Categoría."""
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Usuario
from handlers.base import IntentHandler
from repositories import categoria_repo


class AltaCategoriaHandler(IntentHandler):
    """Registra una nueva categoría personalizada para el usuario."""

    async def manejar(
        self, db: AsyncSession, usuario: Usuario, datos_ia: dict, mensaje_original: str
    ) -> str:
        nueva_categoria = datos_ia.get("categoria", "").strip()

        if not nueva_categoria or nueva_categoria.upper() == "DESCONOCIDA":
            return (
                "No entendí el nombre de la categoría que quieres agregar. "
                "Intenta decir: 'Quiero dar de alta la categoría Transporte'."
            )

        if await categoria_repo.existe(db, usuario.id, nueva_categoria):
            return f"La categoría '{nueva_categoria}' ya existe en tus registros."

        await categoria_repo.crear(db, usuario.id, nueva_categoria)
        return (
            f"¡Hecho! He dado de alta la categoría '{nueva_categoria}'. "
            "Ahora puedes usarla para gastos o presupuestos."
        )
