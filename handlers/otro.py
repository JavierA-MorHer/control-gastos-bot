"""Handler: Intención no reconocida o saludo."""
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Usuario
from handlers.base import IntentHandler


class OtroHandler(IntentHandler):
    """Responde con un mensaje genérico de ayuda."""

    async def manejar(
        self, db: AsyncSession, usuario: Usuario, datos_ia: dict, mensaje_original: str
    ) -> str:
        return (
            "¡Hola! Conmigo puedes:\n"
            "• Dar de alta categorías (ej. 'Alta de categoría Comida')\n"
            "• Registrar gastos (ej. 'Gasté 300 en Comida')\n"
            "• Asignar presupuestos (ej. 'Mi presupuesto de Comida es 1000')\n"
            "• Pedir reportes (ej. 'Mis gastos de esta semana')"
        )
