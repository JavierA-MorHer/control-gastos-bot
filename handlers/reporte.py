"""Handler: Reportes (general y específico)."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Usuario
from handlers.base import IntentHandler
from repositories import gasto_repo
from services.openai_parser import generar_consejo_financiero


class ReporteGeneralHandler(IntentHandler):
    """Responde pidiendo al usuario que especifique un periodo."""

    async def manejar(
        self, db: AsyncSession, usuario: Usuario, datos_ia: dict, mensaje_original: str
    ) -> str:
        return (
            "¿De qué periodo quieres tu reporte? 🗓️ "
            "Puedes decirme: 'gastos de ayer', 'mi reporte semanal', o 'gastos de marzo'."
        )


class ReporteEspecificoHandler(IntentHandler):
    """Genera un reporte de gastos para un periodo concreto."""

    async def manejar(
        self, db: AsyncSession, usuario: Usuario, datos_ia: dict, mensaje_original: str
    ) -> str:
        f_inicio_str = datos_ia.get("fecha_inicio")
        f_fin_str = datos_ia.get("fecha_fin")

        if not f_inicio_str or not f_fin_str:
            return (
                "Entendí que quieres un reporte, pero la IA no logró captar las fechas exactas. "
                "Intenta algo como 'mis gastos de ayer'."
            )

        f_inicio_dt = datetime.strptime(f_inicio_str, "%Y-%m-%d")
        f_fin_dt = datetime.strptime(f_fin_str, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )

        gastos = await gasto_repo.obtener_por_periodo(
            db, usuario.id, f_inicio_dt, f_fin_dt
        )

        if not gastos:
            return (
                f"Revisé tus registros del {f_inicio_str} al {f_fin_str} "
                "y no tienes ningún gasto. ¡Qué buen ahorro! 💸"
            )

        return await self._generar_resumen(gastos, f_inicio_str, f_fin_str)

    # ── Métodos privados ──────────────────────────────────────────────

    @staticmethod
    async def _generar_resumen(
        gastos: list, f_inicio: str, f_fin: str
    ) -> str:
        """Agrupa los gastos por categoría y genera un consejo financiero."""
        totales_cat: dict[str, float] = {}
        total_general = 0.0

        for g in gastos:
            cat = g.categoria
            monto = float(g.monto)
            totales_cat[cat] = totales_cat.get(cat, 0.0) + monto
            total_general += monto

        resumen = f"Periodo: {f_inicio} al {f_fin}\n"
        for cat, tot in totales_cat.items():
            resumen += f"- {cat}: ${tot:,.2f}\n"
        resumen += f"TOTAL GASTADO: ${total_general:,.2f}"

        return await generar_consejo_financiero(resumen)
