import json
import google.generativeai as genai
from core.config import settings
from datetime import datetime

# Configuramos la API Key global
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# Instrucciones del sistema
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
- "monto": coste de lo comprado (float, extraído).
- "categoria": DEBES elegir ESTRICTAMENTE de: ["Comida", "Transporte", "Servicios", "Cuidado Personal", "Salud", "Entretenimiento", "Compras", "Regalos", "Otros"]. Por ejemplo, crema es Cuidado Personal.
- "descripcion": resumen del gasto.

REGLAS PARA "REPORTE_GENERAL":
- El usuario pide un reporte general sin especificar fechas concretas: "dame un reporte", "quiero un informe".

REGLAS PARA "REPORTE_ESPECIFICO":
- El usuario proporciona un contexto de tiempo: "gastos de ayer", "cuanto gaste este mes", "reporte de marzo".
- IMPORTANTE: Usa la fecha exacta que te proporcionaré (HOY ES...) para deducir fechas exactas. Deduce `fecha_inicio` y `fecha_fin` en formato "YYYY-MM-DD". Ejemplo: Si hoy es martes 5 de mayo y piden "ayer", pon "202x-05-04" en ambas. Si piden "este mes", inicio es el primero del mes actual y fin es hoy.

REGLAS PARA "OTRO":
- El usuario saluda ("hola", "buen día") que no requiera el guardado de algo numérico.
"""

try:
    model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_instruction)
except Exception:
    model = genai.GenerativeModel('gemini-2.5-flash')

async def analizar_mensaje_gasto(texto: str) -> dict:
    if not settings.GEMINI_API_KEY:
        raise ValueError("¡La GEMINI_API_KEY no está configurada en .env!")

    hoy = datetime.now().strftime('%A %d de %B de %Y (Formato estructurado: %Y-%m-%d)')
    prompt_con_fecha = f"[INFO DEL SISTEMA: HOY ES {hoy}].\nMensaje del usuario: {texto}"

    try:
        response = await model.generate_content_async(
            prompt_con_fecha,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        
        datos = json.loads(response.text)
        
        return {
            "intencion": str(datos.get("intencion", "OTRO")).upper(),
            "monto": float(datos.get("monto", 0.0)),
            "categoria": str(datos.get("categoria", "Otros")).title(),
            "descripcion": str(datos.get("descripcion", texto)),
            "fecha_inicio": str(datos.get("fecha_inicio", "")),
            "fecha_fin": str(datos.get("fecha_fin", ""))
        }
    except Exception as e:
        print(f"Error interpretando con Gemini: {e}")
        raise ValueError("La Inteligencia Artificial no pudo procesar tu solicitud.")

try:
    advisor_model = genai.GenerativeModel('gemini-2.5-flash', system_instruction="""
Eres el Consejero Financiero del usuario por WhatsApp. Se te dará la información de lo que sumaron sus gastos de un periodo en un texto feo (categoría y cantidad), y las fechas usadas.
Tu tarea es mandarle un mensaje amistoso al usuario, mostrando:
1. Una lista o pequeña tabla estilizada de sus gastos en el reporte. Menciona el total. (No utilices asteriscos molestos, usa negritas limpias *texto*).
2. Dando un pequeño insight/consejo basado en lo que gastó (ej. felicítalo si ahorró, o dale un amistoso regaño si se la pasó en restaurantes).
Respóndele al usuario sabiendo que te llama en WhatsApp y quieres que sea muy fácil de entender, con emojis.
""")
except Exception:
    advisor_model = genai.GenerativeModel('gemini-2.5-flash')

async def generar_consejo_financiero(resumen_texto: str) -> str:
    if not settings.GEMINI_API_KEY:
        return resumen_texto
    try:
        response = await advisor_model.generate_content_async(resumen_texto)
        return response.text
    except Exception as e:
        return f"Aquí está tu resumen de gastos:\n{resumen_texto}\n\n(No se pudo generar consejo automático: {e})"

