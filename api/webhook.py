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
            # Parseo básico con split en vez de IA, para ahorrar créditos
            partes = [p.strip() for p in Body.split('-')]
            
            if len(partes) >= 3:
                # Asumimos que es formato 'Monto - Categoría - Descripción [- Fecha]'
                try:
                    monto = float(partes[0].replace('$', '').replace(',', ''))
                    categoria = partes[1].title()
                    
                    # Intentar leer fecha desde la última parte
                    from datetime import datetime
                    fecha_obj = None
                    posible_fecha = partes[-1].replace('-', '/')
                    try:
                        fecha_obj = datetime.strptime(posible_fecha, "%d/%m/%Y")
                        descripcion = '-'.join(partes[2:-1]).strip()
                    except ValueError:
                        descripcion = '-'.join(partes[2:]).strip()
                    
                    if not descripcion:
                        descripcion = "Sin descripción"
                    
                    if monto <= 0.0:
                         respuesta_texto = "Por favor, ingresa un monto mayor a 0."
                    else:
                        nuevo_gasto = Gasto(
                            usuario_id=usuario.id,
                            monto=monto,
                            categoria=categoria,
                            descripcion=descripcion,
                            mensaje_original=Body
                        )
                        if fecha_obj:
                            nuevo_gasto.fecha_gasto = fecha_obj
                            
                        db.add(nuevo_gasto)
                        await db.commit()
                        
                        fecha_str = f" con fecha {fecha_obj.strftime('%d/%m/%Y')}" if fecha_obj else ""
                        respuesta_texto = f"Se guardó un gasto por ${monto:,.2f} en la categoría '{categoria}'{fecha_str}. ({descripcion})"
                except ValueError:
                    respuesta_texto = "No pude entender el monto. Recuerda usar el formato 'Monto - Categoría - Descripción [- Fecha DD/MM/YYYY opcional]'. (Ej: 300 - Comida - Pizza - 25/03/2026)"
                    
            elif Body.lower().strip() == "reporte":
                # Lógica simple de reporte de todos los gatos que hay
                query = select(Gasto).filter(Gasto.usuario_id == usuario.id)
                resultado_gastos = await db.execute(query)
                lista_gastos = resultado_gastos.scalars().all()
                
                if not lista_gastos:
                    respuesta_texto = "No tienes ningún gasto registrado aún."
                else:
                    totales_cat = {}
                    total_general = 0.0
                    for g in lista_gastos:
                        cat = g.categoria
                        totales_cat[cat] = totales_cat.get(cat, 0.0) + float(g.monto)
                        total_general += float(g.monto)
                        
                    resumen = "Resumen de todos tus gastos:\n"
                    for cat, tot in totales_cat.items():
                        resumen += f"- {cat}: ${tot:,.2f}\n"
                    resumen += f"\nTOTAL GASTADO: ${total_general:,.2f}"
                    
                    respuesta_texto = resumen
            else:
                respuesta_texto = "¡Hola! Para registrar un gasto usa: 'Monto - Categoría - Descripción [- Fecha DD/MM/YYYY opcional]' (Ej: 300 - Comida - Pizza - 20/03/2026). Para ver tu historial envía 'Reporte'."
            
        except Exception as e:
             respuesta_texto = f"❌ Error interno procesando el gasto: {str(e)}"

    # 4. Enviamos la respuesta de vuelta a Twilio usando TwiML (XML)
    response = MessagingResponse()
    response.message(respuesta_texto)
    
    return Response(content=str(response), media_type="application/xml")
