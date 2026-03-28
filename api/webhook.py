from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from twilio.twiml.messaging_response import MessagingResponse

from db.database import get_db
from db.models import Usuario, Gasto

router = APIRouter()

@router.post("/webhook")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Ruta que Twilio llamará cada vez que alguien envíe un mensaje a nuestro bot de WhatsApp.
    """
    
    # 1. Buscamos si el usuario ya existe por su teléfono (ej. 'whatsapp:+123456789')
    resultado = await db.execute(select(Usuario).filter(Usuario.telefono_whatsapp == From))
    usuario = resultado.scalars().first()
    
    # 2. Si no existe en la base de datos, lo registramos
    if not usuario:
        usuario = Usuario(telefono_whatsapp=From)
        db.add(usuario)
        await db.commit()
        await db.refresh(usuario)
        
        # Le damos la bienvenida
        respuesta_texto = "¡Hola! Veo que es tu primera vez por aquí. Ya te registré en la base de datos de Neon. Para guardar un gasto envíame algo con el formato: 'Monto - Categoría - Descripción'."
    else:
        # 3. Si ya existe, tratamos de guardar su gasto
        try:
            # 3. Parseo Avanzado con Inteligencia Artificial (Gemini)
            from services.ai_parser import analizar_mensaje_gasto
            
            datos_gasto = await analizar_mensaje_gasto(Body)
            monto = datos_gasto["monto"]
            categoria = datos_gasto["categoria"]
            descripcion = datos_gasto["descripcion"]
            
            # Si Gemini decide que no hay monto, es un mensaje general/saludo
            if monto <= 0.0:
                respuesta_texto = "¡Hola! Entendí tu mensaje, pero no detecté ningún gasto que guardar. Dime qué compraste y cuánto costó. (Ej: 'Pizza 300' o '150 en la farmacia')"
            else:
                # Guardamos el gasto en la DB conectado con el usuario_id
                nuevo_gasto = Gasto(
                    usuario_id=usuario.id,
                    monto=monto,
                    categoria=categoria,
                    descripcion=descripcion,
                    mensaje_original=Body
                )
                db.add(nuevo_gasto)
                await db.commit()
                
                respuesta_texto = f"Se guardó un gasto por ${monto:,.2f} en la categoría '{categoria}'. ({descripcion})"
            
        except ValueError as e:
            # Si falta la API Key o falla el parseo
            respuesta_texto = f"Error: {str(e)}"
        except Exception as e:
             respuesta_texto = f"❌ Error interno procesando el gasto con la IA: {str(e)}"

    # 4. Enviamos la respuesta de vuelta a Twilio usando TwiML (XML)
    response = MessagingResponse()
    response.message(respuesta_texto)
    
    return Response(content=str(response), media_type="application/xml")
