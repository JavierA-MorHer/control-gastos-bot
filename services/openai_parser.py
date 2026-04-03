"""
Parser de OpenAI.
Responsabilidad única: orquestar prompts + cliente + normalización de respuesta.
No contiene texto de prompts ni lógica HTTP directa.
"""
from datetime import datetime
from services.openai_client import get_openai_client
from services.prompts import construir_prompt_clasificador, PROMPT_CONSEJERO


async def analizar_mensaje(texto: str, categorias_usuario: list[str] | None = None) -> dict:
    """
    Envía el mensaje del usuario a OpenAI y normaliza la respuesta
    en un diccionario con campos estandarizados.
    """
    client = get_openai_client()
    categorias_usuario = categorias_usuario or []
    prompt_sistema = construir_prompt_clasificador(categorias_usuario)

    hoy = datetime.now().strftime("%A %d de %B de %Y (Formato estructurado: %Y-%m-%d)")
    mensaje_usuario = f"[INFO DEL SISTEMA: HOY ES {hoy}].\nMensaje del usuario: {texto}"

    try:
        datos = await client.chat_json(prompt_sistema, mensaje_usuario)

        return {
            "intencion": str(datos.get("intencion", "OTRO")).upper(),
            "monto": float(datos.get("monto", 0.0)),
            "categoria": str(datos.get("categoria", "Otros")).title(),
            "descripcion": str(datos.get("descripcion", texto)),
            "fecha_inicio": str(datos.get("fecha_inicio", "")),
            "fecha_fin": str(datos.get("fecha_fin", "")),
            "confirmado": bool(datos.get("confirmado", False)),
        }
    except Exception as e:
        print(f"Error interpretando con OpenAI: {e}")
        raise ValueError("La Inteligencia Artificial no pudo procesar tu solicitud.")


async def generar_consejo_financiero(resumen_texto: str) -> str:
    """
    Genera un consejo financiero amistoso a partir de un resumen de gastos.
    Si falla, retorna el resumen crudo como fallback.
    """
    try:
        client = get_openai_client()
        return await client.chat_texto(PROMPT_CONSEJERO, resumen_texto)
    except Exception as e:
        return (
            f"Aquí está tu resumen de gastos:\n{resumen_texto}\n\n"
            f"(No se pudo generar consejo automático: {e})"
        )
