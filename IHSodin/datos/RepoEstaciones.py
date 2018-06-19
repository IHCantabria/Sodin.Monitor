# -*- coding: utf-8 -*-

class RepoEstaciones(object):
    '''Clase para gestionar la consulta e insercion de datos de Estaciones'''

    def __init__(self, configuracion, cliente_mongo):
        self.cfg = configuracion
        self.bd_mongo = cliente_mongo

    def obtener_estacion(self, id_estacion):
        return self.bd_mongo.estaciones.find_one({'id':id_estacion})

    def obtener_estaciones(self, codigo_confederacion, solo_activas):
        lista_estaciones = list(self.bd_mongo.estaciones.find({
            'codigoConfederacion': codigo_confederacion}))
        if solo_activas:
            lista_estaciones = self._filtrar_estaciones_activas(lista_estaciones)
        return lista_estaciones

    def obtener_estaciones_activas_de_tipo(self, codigo_tipo):
        lista_estaciones = list(self.bd_mongo.estaciones.find({'activa': True, 'codigoTipo': codigo_tipo}))
        return lista_estaciones

    def obtener_estaciones_de_tipo(self, codigo_confederacion, codigo_tipo, solo_activas):
        lista_estaciones = list(self.bd_mongo.estaciones.find({'codigoConfederacion': codigo_confederacion,
                                                               'codigoTipo': codigo_tipo}))
        if solo_activas:
            lista_estaciones = self._filtrar_estaciones_activas(lista_estaciones)
        return lista_estaciones


    @staticmethod
    def _filtrar_estaciones_activas(lista_estaciones):
        return [estacion for estacion in lista_estaciones if estacion['activa']]
