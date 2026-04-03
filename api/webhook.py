"""
Webhook de Twilio/WhatsApp.
Responsabilidad única: recibir el mensaje, despachar al handler correcto, y responder.
Toda la lógica de negocio vive en handlers/ y repositories/.
"""
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.twiml.messaging_response import MessagingResponse

from db.database import get_db
from repositories import usuario_repo, categoria_repo
from services.openai_parser import analizar_mensaje
from handlers import obtener_handler

router = APIRouter()

MENSAJE_BIENVENIDA = (
    "¡Hola! Veo que es tu primera vez por aquí. Ya te registré. "
    "Para empezar, da de alta tus categorías diciendo: "
    "'Quiero dar de alta la categoría Comida'."
)


@router.post("/webhook")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Punto de entrada de Twilio. Recibe, despacha y responde."""

    # 1. Obtener o crear usuario
    usuario, es_nuevo = await usuario_repo.obtener_o_crear(db, From)

    if es_nuevo:
        respuesta_texto = MENSAJE_BIENVENIDA
    else:
        respuesta_texto = await _procesar_mensaje(db, usuario, Body)

    # 2. Responder con TwiML
    response = MessagingResponse()
    response.message(respuesta_texto)
    return Response(content=str(response), media_type="application/xml")


async def _procesar_mensaje(db: AsyncSession, usuario, mensaje: str) -> str:
    """Orquesta: categorías → IA → estado → handler."""
    try:
        # Obtener categorías del usuario para el prompt
        categorias = await categoria_repo.obtener_nombres(db, usuario.id)

        # Analizar el mensaje con OpenAI
        datos_ia = await analizar_mensaje(mensaje, categorias)
        intencion = datos_ia.get("intencion", "OTRO")

        # Inyectar las categorías en los datos para que los handlers puedan validar
        datos_ia["_categorias_usuario"] = categorias

        # Manejar estado de conversación pendiente (ej. confirmación de presupuesto)
        estado = usuario.estado_conversacion
        if estado and intencion != "CONFIRMACION":
            # El usuario mandó algo diferente a una confirmación → limpiar estado
            await usuario_repo.limpiar_estado(db, usuario)

        # Despachar al handler correcto
        handler = obtener_handler(intencion)
        return await handler.manejar(db, usuario, datos_ia, mensaje)

    except Exception as e:
        return f"❌ Error interno procesando el mensaje: {str(e)}"
