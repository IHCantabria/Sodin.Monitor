# -*- coding: utf-8 -*-

from utiles.Conversor import Conversor

class PostEvento(Conversor):
    """Clase que representa un PostEvento"""

    def __init__(self, props):
        # pylint: disable=C0103
        self.idEvento = props['idEvento']
        self.tipo = props['tipo']
        self.lugar = props['lugar']
        self.idEstacion = props['idEstacion']
        self.coords = props['coords']
        self.medidas = props['medidas']
        self.tweets = props['tweets']
        self.fechaInicio = props['fechaInicio']
        self.fechaFin = props['fechaFin']
