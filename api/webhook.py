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
        # (Aquí podrías meter IA en el futuro para extraer los datos del texto solo)
        try:
            # Parseo básico que asume el formato 'Monto - Categoría - Descripción'
            partes = Body.split("-")
            monto = float(partes[0].strip())
            categoria = partes[1].strip() if len(partes) > 1 else "Sin categoría"
            descripcion = partes[2].strip() if len(partes) > 2 else ""
            
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
            
            respuesta_texto = f"✅ Gasto por ${monto} guardado exitosamente en '{categoria}'."
            
        except ValueError:
            # Si el texto no empieza con un número
             respuesta_texto = "❌ No entendí el formato. Por favor usa: Monto - Categoría - Descripción (Ej: '150 - Comida - Pizza')"

    # 4. Enviamos la respuesta de vuelta a Twilio usando TwiML (XML)
    response = MessagingResponse()
    response.message(respuesta_texto)
    
    return Response(content=str(response), media_type="application/xml")
