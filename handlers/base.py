"""
Handler Base.
Define el contrato que todos los handlers de intención deben cumplir.
"""
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Usuario


class IntentHandler(ABC):
    """Clase base abstracta para todos los handlers de intención."""

    @abstractmethod
    async def manejar(
        self,
        db: AsyncSession,
        usuario: Usuario,
        datos_ia: dict,
        mensaje_original: str,
    ) -> str:
        """
        Procesa la intención y retorna el texto de respuesta para el usuario.

        Args:
            db: Sesión de base de datos.
            usuario: Instancia del usuario que envió el mensaje.
            datos_ia: Diccionario normalizado devuelto por el parser de OpenAI.
            mensaje_original: Texto original del mensaje del usuario (Body).

        Returns:
            Texto de respuesta que se enviará por WhatsApp.
        """
        ...
