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
            # Parseo Avanzado con Inteligencia Artificial (OpenAI)
            from services.openai_parser import analizar_mensaje_gasto_openai, generar_consejo_financiero_openai
            from datetime import datetime
            
            datos_ia = await analizar_mensaje_gasto_openai(Body)
            intencion = datos_ia.get("intencion", "OTRO")
            
            if intencion == "GASTO":
                monto = datos_ia["monto"]
                categoria = datos_ia["categoria"]
                descripcion = datos_ia["descripcion"]
                
                # Si OpenAI decide que no hay monto
                if monto <= 0.0:
                    respuesta_texto = "¡Hola! Entendí tu mensaje, pero no detecté ningún gasto que guardar. Dime qué compraste y cuánto costó. (Ej: 'Pizza 300')"
                else:
                    nuevo_gasto = Gasto(
                        usuario_id=usuario.id,
                        monto=monto,
                        categoria=categoria,
                        descripcion=descripcion,
                        mensaje_original=Body
                    )
                    
                    # Guardar la fecha deducida por IA si la indicó
                    fecha_str = datos_ia.get("fecha_inicio")
                    fecha_obj = None
                    if fecha_str:
                        try:
                            # OpenAI nos da YYYY-MM-DD
                            fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
                            nuevo_gasto.fecha_gasto = fecha_obj
                        except ValueError:
                            pass
                            
                    db.add(nuevo_gasto)
                    await db.commit()
                    
                    lbl_fecha = f" con fecha {fecha_obj.strftime('%d/%m/%Y')}" if fecha_obj else ""
                    respuesta_texto = f"Se guardó un gasto por ${monto:,.2f} en la categoría '{categoria}'{lbl_fecha}. ({descripcion})"
                    
            elif intencion == "REPORTE_GENERAL":
                respuesta_texto = "¿De qué periodo quieres tu reporte? 🗓️ Puedes decirme: 'gastos de ayer', 'mi reporte semanal', o 'gastos de marzo'."
                
            elif intencion == "REPORTE_ESPECIFICO":
                f_inicio_str = datos_ia.get("fecha_inicio")
                f_fin_str = datos_ia.get("fecha_fin")
                
                if not f_inicio_str or not f_fin_str:
                    respuesta_texto = "Entendí que quieres un reporte, pero la IA no logró captar las fechas exactas. Intenta algo como 'mis gastos de ayer'."
                else:
                    # Convertimos string YYYY-MM-DD a datetime
                    # El inicio del día 00:00:00
                    f_inicio_dt = datetime.strptime(f_inicio_str, "%Y-%m-%d")
                    # El final del día 23:59:59
                    f_fin_dt = datetime.strptime(f_fin_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                    
                    # Consultamos base de datos
                    query = select(Gasto).filter(
                        Gasto.usuario_id == usuario.id,
                        Gasto.fecha_gasto >= f_inicio_dt,
                        Gasto.fecha_gasto <= f_fin_dt
                    )
                    resultado_gastos = await db.execute(query)
                    lista_gastos = resultado_gastos.scalars().all()
                    
                    if not lista_gastos:
                        respuesta_texto = f"Revisé tus registros del {f_inicio_str} al {f_fin_str} y no tienes ningún gasto. ¡Qué buen ahorro! 💸"
                    else:
                        # Agrupar por categoría
                        totales_cat = {}
                        total_general = 0.0
                        for g in lista_gastos:
                            cat = g.categoria
                            totales_cat[cat] = totales_cat.get(cat, 0.0) + float(g.monto)
                            total_general += float(g.monto)
                            
                        # Resumen crudo
                        resumen = f"Periodo: {f_inicio_str} al {f_fin_str}\n"
                        for cat, tot in totales_cat.items():
                            resumen += f"- {cat}: ${tot:,.2f}\n"
                        resumen += f"TOTAL GASTADO: ${total_general:,.2f}"
                        
                        # Segunda llamada IA
                        respuesta_texto = await generar_consejo_financiero_openai(resumen)
                        
            else: # intencion == OTRO
                respuesta_texto = "¡Hola! Conmigo puedes registrar tus gastos diarios (ej. 'comí en la calle 250') o pedirme reportes (ej. 'cuánto he gastado esta semana')."
            
        except Exception as e:
             respuesta_texto = f"❌ Error interno procesando el gasto: {str(e)}"

    # 4. Enviamos la respuesta de vuelta a Twilio usando TwiML (XML)
    response = MessagingResponse()
    response.message(respuesta_texto)
    
    return Response(content=str(response), media_type="application/xml")
