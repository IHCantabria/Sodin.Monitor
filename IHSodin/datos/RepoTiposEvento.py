# -*- coding: utf-8 -*-
class RepoTiposEvento(object):
    '''Clase para gestionar la consulta e insercion de datos de Variables'''

    def __init__(self, configuracion, cliente_mongo):
        self.cfg = configuracion
        self.bd_mongo = cliente_mongo

    def obtener_tipos_evento(self):
        return list(self.bd_mongo.tiposEvento.find({}))

    def obtener_tipo_evento(self, nombre):
        return self.bd_mongo.tiposEvento.find_one({'nombre':nombre})

    def obtener_tipo_evento_costero(self):
        return self.bd_mongo.tiposEvento.find_one({'nombre': self.cfg.TIPO_EVENTO_COSTERO})

    def obtener_tipo_evento_fluvial(self):
        return self.bd_mongo.tiposEvento.find_one({'nombre': self.cfg.TIPO_EVENTO_FLUVIAL})
