# -*- coding: utf-8 -*-

from utiles.Conversor import Conversor

class Evento(Conversor):
    """Clase que representa un evento"""

    def __init__(self, props):
        # pylint: disable=C0103
        self.fechaInicio = props['fechaInicio']
        self.fechaFin = props['fechaFin']
        self.codigoTipo = props['codigoTipo']
        self.idEstacion = props['idEstacion']
        self.activo = props['activo']
        self.toponimos = props['toponimos']
        self.datosAemet = props['datosAemet']
        self.datosPuertos = props['datosPuertos']
        self.datosConfederaciones = props['datosConfederaciones']
        self.datosTwitter = props['datosTwitter']
