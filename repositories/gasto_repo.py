"""
Repositorio de Gastos.
Responsabilidad única: lectura y escritura de la entidad Gasto.
"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models import Gasto


async def crear(
    db: AsyncSession,
    usuario_id: int,
    monto: float,
    categoria: str,
    descripcion: str,
    mensaje_original: str,
    fecha: datetime | None = None,
) -> Gasto:
    """Crea un nuevo registro de gasto."""
    gasto = Gasto(
        usuario_id=usuario_id,
        monto=monto,
        categoria=categoria,
        descripcion=descripcion,
        mensaje_original=mensaje_original,
    )
    if fecha:
        gasto.fecha_gasto = fecha
    db.add(gasto)
    await db.commit()
    return gasto


async def obtener_por_periodo(
    db: AsyncSession,
    usuario_id: int,
    fecha_inicio: datetime,
    fecha_fin: datetime,
) -> list[Gasto]:
    """Retorna todos los gastos de un usuario en un rango de fechas."""
    query = select(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.fecha_gasto >= fecha_inicio,
        Gasto.fecha_gasto <= fecha_fin,
    )
    resultado = await db.execute(query)
    return resultado.scalars().all()
