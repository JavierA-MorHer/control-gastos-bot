"""
Repositorio de Presupuestos.
Responsabilidad única: lectura y escritura de la entidad Presupuesto.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models import Presupuesto


async def obtener_por_categoria(
    db: AsyncSession, usuario_id: int, categoria: str
) -> Presupuesto | None:
    """Busca un presupuesto existente por usuario y categoría."""
    resultado = await db.execute(
        select(Presupuesto).filter(
            Presupuesto.usuario_id == usuario_id,
            Presupuesto.categoria == categoria,
        )
    )
    return resultado.scalars().first()


async def crear(
    db: AsyncSession, usuario_id: int, categoria: str, monto: float
) -> Presupuesto:
    """Crea un nuevo presupuesto."""
    presupuesto = Presupuesto(
        usuario_id=usuario_id, categoria=categoria, monto=monto
    )
    db.add(presupuesto)
    await db.commit()
    return presupuesto


async def actualizar_monto(
    db: AsyncSession, presupuesto: Presupuesto, nuevo_monto: float
) -> None:
    """Actualiza el monto de un presupuesto existente."""
    presupuesto.monto = nuevo_monto
    await db.commit()
