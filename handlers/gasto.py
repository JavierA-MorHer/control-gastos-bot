"""Handler: Registro de Gasto."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Usuario
from handlers.base import IntentHandler
from repositories import gasto_repo


class GastoHandler(IntentHandler):
    """Registra un nuevo gasto del usuario."""

    async def manejar(
        self, db: AsyncSession, usuario: Usuario, datos_ia: dict, mensaje_original: str
    ) -> str:
        monto = datos_ia["monto"]
        categoria = datos_ia["categoria"]
        descripcion = datos_ia["descripcion"]

        if monto <= 0.0:
            return "Entendí tu mensaje, pero no detecté ningún gasto que guardar. (Ej: 'Gasté 300 en Comida')"

        if self._categoria_invalida(categoria, datos_ia.get("_categorias_usuario", [])):
            return (
                "No reconocí la categoría. Solo puedes registrar gastos en categorías tuyas. "
                "Para crear una nueva di: 'Alta de categoría [nombre]'."
            )

        # Parsear fecha si la IA la dedujo
        fecha_obj = self._parsear_fecha(datos_ia.get("fecha_inicio"))

        gasto = await gasto_repo.crear(
            db,
            usuario_id=usuario.id,
            monto=monto,
            categoria=categoria,
            descripcion=descripcion,
            mensaje_original=mensaje_original,
            fecha=fecha_obj,
        )

        lbl_fecha = f" con fecha {fecha_obj.strftime('%d/%m/%Y')}" if fecha_obj else ""
        return f"Se guardó un gasto por ${monto:,.2f} en '{categoria}'{lbl_fecha}. ({descripcion})"

    # ── Métodos privados ──────────────────────────────────────────────

    @staticmethod
    def _categoria_invalida(categoria: str, categorias_existentes: list[str]) -> bool:
        """Valida que la categoría exista en la lista del usuario."""
        if categoria == "DESCONOCIDA":
            return True
        if categorias_existentes and categoria not in categorias_existentes:
            return True
        return False

    @staticmethod
    def _parsear_fecha(fecha_str: str | None) -> datetime | None:
        """Intenta convertir una fecha string YYYY-MM-DD a datetime."""
        if not fecha_str:
            return None
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d")
        except ValueError:
            return None
