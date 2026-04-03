"""Handler: Presupuesto."""
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Usuario
from handlers.base import IntentHandler
from repositories import presupuesto_repo, usuario_repo


class PresupuestoHandler(IntentHandler):
    """Registra o solicita actualización de un presupuesto por categoría."""

    async def manejar(
        self, db: AsyncSession, usuario: Usuario, datos_ia: dict, mensaje_original: str
    ) -> str:
        monto = datos_ia["monto"]
        categoria = datos_ia["categoria"]
        categorias_existentes = datos_ia.get("_categorias_usuario", [])

        if monto <= 0.0:
            return (
                "Entendí que quieres un presupuesto, pero no me indicaste cuánto. "
                "Prueba decir 'mi presupuesto de Comida es 1000'."
            )

        if self._categoria_invalida(categoria, categorias_existentes):
            return (
                "No reconocí la categoría. Antes de asignar un presupuesto a una categoría nueva, "
                "debes crearla. Di: 'Quiero dar de alta la categoría [nombre]'."
            )

        presupuesto = await presupuesto_repo.obtener_por_categoria(db, usuario.id, categoria)

        if presupuesto:
            # Ya existe → pedir confirmación al usuario
            await usuario_repo.guardar_estado(db, usuario, {
                "accion": "CONFIRMAR_PRESUPUESTO",
                "categoria": categoria,
                "monto": monto,
            })
            return (
                f"Ya tienes un presupuesto para '{categoria}' de ${presupuesto.monto:,.2f}. "
                f"¿Quieres actualizarlo a ${monto:,.2f}? (Responde 'sí' o 'no')"
            )

        # No existe → crear directamente
        await presupuesto_repo.crear(db, usuario.id, categoria, monto)
        return f"¡Listo! He registrado un presupuesto de ${monto:,.2f} para la categoría '{categoria}'."

    @staticmethod
    def _categoria_invalida(categoria: str, categorias_existentes: list[str]) -> bool:
        if categoria == "DESCONOCIDA":
            return True
        if categorias_existentes and categoria not in categorias_existentes:
            return True
        return False
