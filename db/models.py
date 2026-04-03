from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    telefono_whatsapp = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100), nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now())
    
    # Campo para manejar el estado de la conversacion (ej. esperando que confirme actualizacion de presupuesto)
    estado_conversacion = Column(JSONB, nullable=True)

    # Relaciones
    gastos = relationship("Gasto", back_populates="usuario", cascade="all, delete-orphan")
    presupuestos = relationship("Presupuesto", back_populates="usuario", cascade="all, delete-orphan")
    categorias_personalizadas = relationship("CategoriaUsuario", back_populates="usuario", cascade="all, delete-orphan")

class CategoriaUsuario(Base):
    __tablename__ = "categorias_usuario"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String(50), nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())

    usuario = relationship("Usuario", back_populates="categorias_personalizadas")

class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    categoria = Column(String(50), nullable=False)
    monto = Column(DECIMAL(12, 2), nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())

    usuario = relationship("Usuario", back_populates="presupuestos")

class Gasto(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    monto = Column(DECIMAL(12, 2), nullable=False)
    categoria = Column(String(50), nullable=False)
    descripcion = Column(Text, nullable=True)
    mensaje_original = Column(Text, nullable=False)
    metadatos = Column(JSONB, nullable=True)
    fecha_gasto = Column(DateTime, server_default=func.now())

    # Relación inversa con Usuario
    usuario = relationship("Usuario", back_populates="gastos")
