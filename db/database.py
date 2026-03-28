from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from core.config import settings

# Motor asíncrono que se conecta a tu base de datos Neon
engine = create_async_engine(settings.NEON_DATABASE_URL, echo=False)

# Creador de sesiones asíncronas para la DB
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

# Función inyectable ("Dependency") para usar la DB en las rutas de FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
