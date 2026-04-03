"""
Repositorio de Usuarios.
Responsabilidad única: lectura y escritura de la entidad Usuario.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models import Usuario


async def obtener_por_telefono(db: AsyncSession, telefono: str) -> Usuario | None:
    """Busca un usuario por su número de WhatsApp."""
    resultado = await db.execute(
        select(Usuario).filter(Usuario.telefono_whatsapp == telefono)
    )
    return resultado.scalars().first()


async def crear(db: AsyncSession, telefono: str) -> Usuario:
    """Registra un nuevo usuario y lo devuelve con su id asignado."""
    usuario = Usuario(telefono_whatsapp=telefono)
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


async def obtener_o_crear(db: AsyncSession, telefono: str) -> tuple[Usuario, bool]:
    """
    Retorna (usuario, es_nuevo).
    Si el usuario no existía, lo crea automáticamente.
    """
    usuario = await obtener_por_telefono(db, telefono)
    if usuario:
        return usuario, False
    return await crear(db, telefono), True


async def guardar_estado(db: AsyncSession, usuario: Usuario, estado: dict) -> None:
    """Guarda un estado temporal de conversación en el usuario."""
    # Preservar el historial si existe
    if usuario.estado_conversacion and "historial" in usuario.estado_conversacion:
        estado["historial"] = usuario.estado_conversacion["historial"]
    
    usuario.estado_conversacion = estado
    db.add(usuario)
    await db.commit()


async def limpiar_estado(db: AsyncSession, usuario: Usuario) -> None:
    """Limpia el estado temporal de conversación (preservando el historial)."""
    if usuario.estado_conversacion and "historial" in usuario.estado_conversacion:
        usuario.estado_conversacion = {"historial": usuario.estado_conversacion["historial"]}
    else:
        usuario.estado_conversacion = None
    db.add(usuario)
    await db.commit()


from sqlalchemy.orm.attributes import flag_modified


async def agregar_mensaje_historial(db: AsyncSession, usuario: Usuario, role: str, content: str) -> None:
    """
    Agrega un mensaje al historial de corto plazo.
    Mantiene un máximo de 6 mensajes (las últimas 3 interacciones).
    """
    estado = usuario.estado_conversacion or {}
    historial = estado.get("historial", [])
    
    historial.append({"role": role, "content": content})
    
    # Mantener solo los últimos 6
    if len(historial) > 6:
        historial = historial[-6:]
        
    estado["historial"] = historial
    usuario.estado_conversacion = estado
    
    # IMPORTANTE: Notificar a SQLAlchemy que la columna JSON mutó
    flag_modified(usuario, "estado_conversacion")
    
    db.add(usuario)
    await db.commit()
