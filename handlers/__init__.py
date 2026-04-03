"""
Registro de Handlers.
Open/Closed: para agregar una intención nueva, solo crea un handler
y agrégalo al diccionario HANDLERS. Cero cambios en webhook.py.
"""
from handlers.alta_categoria import AltaCategoriaHandler
from handlers.gasto import GastoHandler
from handlers.presupuesto import PresupuestoHandler
from handlers.confirmacion import ConfirmacionHandler
from handlers.reporte import ReporteGeneralHandler, ReporteEspecificoHandler
from handlers.otro import OtroHandler
from handlers.base import IntentHandler

# Mapeo intención → handler concreto
HANDLERS: dict[str, IntentHandler] = {
    "ALTA_CATEGORIA": AltaCategoriaHandler(),
    "GASTO": GastoHandler(),
    "PRESUPUESTO": PresupuestoHandler(),
    "CONFIRMACION": ConfirmacionHandler(),
    "REPORTE_GENERAL": ReporteGeneralHandler(),
    "REPORTE_ESPECIFICO": ReporteEspecificoHandler(),
    "OTRO": OtroHandler(),
}


def obtener_handler(intencion: str) -> IntentHandler:
    """Retorna el handler correspondiente a la intención, o el handler 'OTRO' como fallback."""
    return HANDLERS.get(intencion, HANDLERS["OTRO"])
