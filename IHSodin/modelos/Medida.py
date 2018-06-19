
from utiles.Conversor import Conversor

class Medida(Conversor):
    """Clase que representa una medida"""

    def __init__(self, props):
        # pylint: disable=C0103
        self.idEstacion = props['idEstacion']
        self.codigoVariable = props['codigoVariable']
        self.fecha = props['fecha']
        self.valor = props['valor']
