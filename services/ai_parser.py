import json
import google.generativeai as genai
from core.config import settings

# Configuramos la API Key global
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# Instrucciones del sistema para forzar el formato
system_instruction = """
Eres un asistente experto en finanzas personales. Tu único objetivo es extraer datos sobre gastos a partir de mensajes libres.
Devuelve SIEMPRE y ÚNICAMENTE un objeto JSON válido con las siguientes 3 claves:
- "monto": número flotante extraído del gasto (sin comas ni símbolos). Devuelve 0.0 si el usuario no dice ninguna cantidad de dinero.
- "categoria": DEBES elegir ESTRICTAMENTE una de las siguientes categorías exactas: 
  ["Comida", "Transporte", "Servicios", "Cuidado Personal", "Salud", "Entretenimiento", "Compras", "Regalos", "Otros"]. 
  Por ejemplo, cremas, talco y desodorantes van siempre a "Cuidado Personal".
- "descripcion": resumen muy corto de en qué se gastó.

Si el mensaje del usuario no parece ser un gasto sino un saludo (hola, buen día) o una consulta general, devuelve monto 0.0, categoria "General" y descripcion "Mensaje general".
"""

# Inicializamos el modelo de IA (flash es la versión más rápida y recomendada para esto)
# Usando "gemini-2.5-flash" porque soporta "response_mime_type" y "system_instruction"
try:
    model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_instruction)
except Exception:
    # Fallback si por alguna razón falla el modelo con system instruct
    model = genai.GenerativeModel('gemini-2.5-flash')

async def analizar_mensaje_gasto(texto: str) -> dict:
    """Consulte la IA Gemini para entender el mensaje y extraer JSON."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("¡La GEMINI_API_KEY no está configurada en .env!")

    try:
        # Enviamos la consulta obligando a que responda en JSON
        response = await model.generate_content_async(
            texto,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        
        datos = json.loads(response.text)
        
        return {
            "monto": float(datos.get("monto", 0.0)),
            "categoria": str(datos.get("categoria", "Otros")).title(),
            "descripcion": str(datos.get("descripcion", texto))
        }
    except Exception as e:
        print(f"Error interpretando con Gemini: {e}")
        raise ValueError("La Inteligencia Artificial no pudo procesar tu gasto.")
