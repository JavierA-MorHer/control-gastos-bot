"""
Repositorio de Categorías personalizadas.
Responsabilidad única: lectura y escritura de la entidad CategoriaUsuario.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models import CategoriaUsuario


async def obtener_nombres(db: AsyncSession, usuario_id: int) -> list[str]:
    """Retorna la lista de nombres de categoría del usuario."""
    resultado = await db.execute(
        select(CategoriaUsuario).filter(CategoriaUsuario.usuario_id == usuario_id)
    )
    return [c.nombre for c in resultado.scalars().all()]


async def existe(db: AsyncSession, usuario_id: int, nombre: str) -> bool:
    """Comprueba si una categoría ya existe (case-insensitive)."""
    nombres = await obtener_nombres(db, usuario_id)
    return nombre.lower() in [n.lower() for n in nombres]


async def crear(db: AsyncSession, usuario_id: int, nombre: str) -> CategoriaUsuario:
    """Crea una nueva categoría personalizada."""
    categoria = CategoriaUsuario(usuario_id=usuario_id, nombre=nombre)
    db.add(categoria)
    await db.commit()
    return categoria
