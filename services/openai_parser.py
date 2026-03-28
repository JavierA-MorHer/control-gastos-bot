import json
from openai import AsyncOpenAI
from core.config import settings
from datetime import datetime

# Cliente de OpenAI (se inicializará si hay API key)
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

# Instrucciones del sistema principal
system_instruction = """
Eres un asistente financiero. Tienes 2 tareas: categorizar gastos o entender solicitudes de reportes.
Devuelve SIEMPRE un JSON válido con esta estructura estricta:
{
  "intencion": "GASTO" o "REPORTE_GENERAL" o "REPORTE_ESPECIFICO" o "OTRO",
  "monto": 0.0,
  "categoria": "...",
  "descripcion": "...",
  "fecha_inicio": "YYYY-MM-DD",
  "fecha_fin": "YYYY-MM-DD"
}

REGLAS PARA "GASTO":
- El usuario habla de un gasto o compra, ejemplo: "pizza 300", "me gasté 100 en un taxi", "super 500".
- "monto": coste de lo comprado (number float).
- "categoria": DEBES elegir ESTRICTAMENTE de: ["Comida", "Transporte", "Servicios", "Cuidado Personal", "Salud", "Entretenimiento", "Compras", "Regalos", "Otros"]. Por ejemplo, crema es Cuidado Personal.
- "descripcion": resumen del gasto.

REGLAS PARA "REPORTE_GENERAL":
- El usuario pide un reporte general sin especificar fechas concretas: "dame un reporte", "quiero un informe".

REGLAS PARA "REPORTE_ESPECIFICO":
- El usuario proporciona un contexto de tiempo: "gastos de ayer", "cuanto gaste este mes", "reporte de marzo".
- IMPORTANTE: Usa la fecha exacta que te proporcionaré (HOY ES...) para deducir fechas exactas. Deduce `fecha_inicio` y `fecha_fin` en formato "YYYY-MM-DD". Ejemplo: Si hoy es martes 5 y piden "ayer", pon "YYYY-MM-04".

REGLAS PARA "OTRO":
- El usuario saluda ("hola", "buen día") que no requiera el guardado de algo numérico.
"""

async def analizar_mensaje_gasto_openai(texto: str) -> dict:
    if not client:
        raise ValueError("¡La OPENAI_API_KEY no está configurada en .env!")

    hoy = datetime.now().strftime('%A %d de %B de %Y (Formato estructurado: %Y-%m-%d)')
    mensaje_usuario = f"[INFO DEL SISTEMA: HOY ES {hoy}].\nMensaje del usuario: {texto}"

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": mensaje_usuario}
            ]
        )
        
        contenido = response.choices[0].message.content
        datos = json.loads(contenido)
        
        return {
            "intencion": str(datos.get("intencion", "OTRO")).upper(),
            "monto": float(datos.get("monto", 0.0)),
            "categoria": str(datos.get("categoria", "Otros")).title(),
            "descripcion": str(datos.get("descripcion", texto)),
            "fecha_inicio": str(datos.get("fecha_inicio", "")),
            "fecha_fin": str(datos.get("fecha_fin", ""))
        }
    except Exception as e:
        print(f"Error interpretando con OpenAI: {e}")
        raise ValueError("La Inteligencia Artificial no pudo procesar tu solicitud.")

# Instrucciones del sistema para el consejero
advisor_instruction = """
Eres el Consejero Financiero del usuario por WhatsApp. Se te dará la información de lo que sumaron sus gastos de un periodo en un texto (categoría y cantidad), y las fechas usadas.
Tu tarea es mandarle un mensaje amistoso al usuario, mostrando:
1. Una lista o pequeña tabla estilizada de sus gastos en el reporte. Menciona el total. (No utilices asteriscos molestos, usa negritas limpias *texto*).
2. Dando un pequeño insight/consejo basado en lo que gastó (ej. felicítalo si ahorró, o dale un amistoso regaño si se la pasó en restaurantes).
Respóndele al usuario sabiendo que te llama en WhatsApp y quieres que sea muy fácil de entender, con emojis.
"""

async def generar_consejo_financiero_openai(resumen_texto: str) -> str:
    if not client:
        return resumen_texto
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": advisor_instruction},
                {"role": "user", "content": resumen_texto}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Aquí está tu resumen de gastos:\n{resumen_texto}\n\n(No se pudo generar consejo automático: {e})"
