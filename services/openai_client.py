"""
Cliente de OpenAI.
Responsabilidad única: gestionar la conexión con el API de OpenAI
y exponer métodos genéricos de chat (JSON y texto libre).
No conoce la lógica de negocio ni los prompts específicos.
"""
import json
from openai import AsyncOpenAI
from core.config import settings


class OpenAIClient:
    """Wrapper delgado sobre el SDK de OpenAI."""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("¡La OPENAI_API_KEY no está configurada en .env!")
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"

    async def chat_json(self, system: str, user: str) -> dict:
        """Envía un chat y espera un JSON parseado como respuesta."""
        response = await self._client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        contenido = response.choices[0].message.content
        return json.loads(contenido)

    async def chat_texto(self, system: str, user: str) -> str:
        """Envía un chat y devuelve la respuesta como texto plano."""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content


# Instancia única (singleton a nivel de módulo)
_client: OpenAIClient | None = None


def get_openai_client() -> OpenAIClient:
    """Retorna la instancia compartida del cliente."""
    global _client
    if _client is None:
        _client = OpenAIClient()
    return _client
