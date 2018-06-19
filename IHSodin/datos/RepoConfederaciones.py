# -*- coding: utf-8 -*-
from proveedores.CHSil import CHSil
from proveedores.CHCantabrico import CHCantabrico
from proveedores.CHEbro import CHEbro
from proveedores.BoyasPuertos import BoyasPuertos

class RepoConfederaciones(object):
    '''Clase para gestionar la consulta e insercion de datos de Confederaciones'''

    def __init__(self, configuracion, cliente_mongo):
        self.cfg = configuracion
        self.bd_mongo = cliente_mongo

    def obtener_confederacion(self, codigo_confederacion):
        return self.bd_mongo.confederaciones.find_one({'codigo': codigo_confederacion})

    def obtener_confederaciones(self):
        return list(self.bd_mongo.confederaciones.find({}))

    # pylint: disable=R0201
    def obtener_proveedor_saih(self, confederacion):
        chc = CHCantabrico(self.cfg)
        chsil = CHSil()
        chebro = CHEbro()

        if confederacion['alias'] == chc.tipo_proveedor():
            return chc
        if confederacion['alias'] == chsil.tipo_proveedor():
            return chsil
        if confederacion['alias'] == chebro.tipo_proveedor():
            return chebro
        return None

    def obtener_proveedor_boyas(self):
        boyas_puertos = BoyasPuertos()
        return boyas_puertos
