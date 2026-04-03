"""Handler: Consulta de Presupuesto (cuánto llevo gastado/cuánto me queda)."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Usuario
from handlers.base import IntentHandler
from repositories import presupuesto_repo, gasto_repo


class ConsultaPresupuestoHandler(IntentHandler):
    """Consulta el estado de un presupuesto frente a lo gastado en el mes actual."""

    async def manejar(
        self, db: AsyncSession, usuario: Usuario, datos_ia: dict, mensaje_original: str
    ) -> str:
        categoria = datos_ia.get("categoria", "")
        categorias_existentes = datos_ia.get("_categorias_usuario", [])

        if not categoria or categoria == "DESCONOCIDA" or (categorias_existentes and categoria not in categorias_existentes):
            return "No reconocí la categoría. Por favor, indícame de qué categoría quieres consultar el presupuesto (ej. 'Mi presupuesto de comida')."

        # Obtener presupuesto configurado
        presupuesto = await presupuesto_repo.obtener_por_categoria(db, usuario.id, categoria)
        if not presupuesto:
            return f"Actualmente no tienes un presupuesto configurado para '{categoria}'. Puedes crear uno diciendo: 'Mi presupuesto de {categoria} es X'."

        # Obtener gastos del mes actual para esta categoría
        hoy = datetime.now()
        # Primer día del mes actual
        fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Para el reporte, podemos tomar hasta fin de mes o simplemente hasta ahora, pero obtener_por_periodo incluye todo hasta f_fin
        gastos = await gasto_repo.obtener_por_periodo(db, usuario.id, fecha_inicio, hoy)

        # Filtrar solo la categoría solicitada
        gastos_categoria = [g for g in gastos if g.categoria.lower() == categoria.lower()]

        total_gastado = sum(float(g.monto) for g in gastos_categoria)
        monto_presupuesto = float(presupuesto.monto)
        restante = monto_presupuesto - total_gastado

        if restante > 0:
            return (
                f"📊 *Estado de {categoria}*\n"
                f"• Presupuesto: ${monto_presupuesto:,.2f}\n"
                f"• Gastado este mes: ${total_gastado:,.2f}\n"
                f"• Te quedan: *${restante:,.2f}* disponibles."
            )
        elif restante == 0:
            return (
                f"📊 *Estado de {categoria}*\n"
                f"Has gastado exactamente los ${total_gastado:,.2f} de tu presupuesto. ¡Estás al límite!"
            )
        else:
            return (
                f"📊 *Estado de {categoria}*\n"
                f"• Presupuesto: ${monto_presupuesto:,.2f}\n"
                f"• Gastado este mes: ${total_gastado:,.2f}\n"
                f"🚨 ¡Te has pasado por *${abs(restante):,.2f}*!"
            )
