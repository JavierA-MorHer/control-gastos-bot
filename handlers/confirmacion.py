"""Handler: Confirmación (sí/no) de operaciones pendientes."""
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Usuario
from handlers.base import IntentHandler
from repositories import presupuesto_repo, usuario_repo


class ConfirmacionHandler(IntentHandler):
    """
    Procesa respuestas de confirmación del usuario ("sí" / "no")
    cuando hay una acción pendiente en su estado de conversación.
    """

    async def manejar(
        self, db: AsyncSession, usuario: Usuario, datos_ia: dict, mensaje_original: str
    ) -> str:
        estado = usuario.estado_conversacion
        if not estado:
            return "No hay ninguna acción pendiente para confirmar."

        accion = estado.get("accion")

        if accion == "CONFIRMAR_PRESUPUESTO":
            return await self._confirmar_presupuesto(db, usuario, datos_ia, estado)

        # Acción desconocida → limpiar estado
        await usuario_repo.limpiar_estado(db, usuario)
        return "No entendí qué confirmar. Intenta de nuevo."

    # ── Métodos privados ──────────────────────────────────────────────

    async def _confirmar_presupuesto(
        self, db: AsyncSession, usuario: Usuario, datos_ia: dict, estado: dict
    ) -> str:
        categoria = estado.get("categoria")
        monto = estado.get("monto")

        if datos_ia.get("confirmado"):
            presupuesto = await presupuesto_repo.obtener_por_categoria(
                db, usuario.id, categoria
            )
            if presupuesto:
                await presupuesto_repo.actualizar_monto(db, presupuesto, monto)
            else:
                await presupuesto_repo.crear(db, usuario.id, categoria, monto)

            await usuario_repo.limpiar_estado(db, usuario)
            return f"¡Listo! He actualizado tu presupuesto de '{categoria}' a ${monto:,.2f}."

        # Rechazado
        await usuario_repo.limpiar_estado(db, usuario)
        return "Entendido, dejaremos tu presupuesto como estaba."
