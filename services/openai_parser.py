import json
from openai import AsyncOpenAI
from core.config import settings
from datetime import datetime

# Cliente de OpenAI (se inicializará si hay API key)
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

system_instruction = """
Eres un asistente financiero. Tienes 3 tareas principales: categorizar gastos, entender solicitudes de presupuestos, o entender solicitudes de reportes.
También debes reconocer cuando el usuario confirma o rechaza algo.
Devuelve SIEMPRE un JSON válido con esta estructura estricta:
{
  "intencion": "GASTO" o "REPORTE_GENERAL" o "REPORTE_ESPECIFICO" o "PRESUPUESTO" o "CONFIRMACION" o "OTRO",
  "monto": 0.0,
  "categoria": "...",
  "descripcion": "...",
  "fecha_inicio": "YYYY-MM-DD",
  "fecha_fin": "YYYY-MM-DD",
  "confirmado": true o false
}

REGLAS PARA "GASTO":
- El usuario habla de un gasto o compra, ejemplo: "pizza 300".
- "monto": coste (number float).
- "categoria": ESTRICTAMENTE de: ["Comida", "Transporte", "Servicios", "Cuidado Personal", "Salud", "Entretenimiento", "Compras", "Regalos", "Otros"].
- "descripcion": resumen.

REGLAS PARA "PRESUPUESTO":
- El usuario indica cuánto planea gastar en una categoría, ej: "mi presupuesto de comida es 1000", "1000 para restaurantes de presupuesto".
- "monto": cantidad asignada.
- "categoria": Misma lista del GASTO.

REGLAS PARA "CONFIRMACION":
- El usuario dice "sí", "claro", "actualízalo", "no", "cancela".
- "confirmado": true si es afirmativo, false si es negativo.

REGLAS PARA "REPORTE_GENERAL" y "REPORTE_ESPECIFICO":
- Para GENERAL: "dame un reporte", "quiero un informe".
- Para ESPECIFICO: Da un periodo "gastos de ayer". Deduce fechas EXACTAS "YYYY-MM-DD" usando (HOY ES...).

REGLAS PARA "OTRO":
- Saludos u otras charlas ("hola").
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
            "fecha_fin": str(datos.get("fecha_fin", "")),
            "confirmado": bool(datos.get("confirmado", False))
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
