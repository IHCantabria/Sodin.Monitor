# -*- coding: utf-8 -*-


class RepoVariables(object):
    '''Clase para gestionar la consulta e insercion de datos de Variables'''

    def __init__(self, configuracion, cliente_mongo):
        self.cfg = configuracion
        self.bd_mongo = cliente_mongo

    def obtener_variables_de_tipo(self, cod_tipo):
        return list(self.bd_mongo.variables.find({'codigoTipoEvento': cod_tipo}))

    def obtener_variable(self, codigo):
        return self.bd_mongo.variables.find_one({'codigo':codigo})

    def obtener_variable_por_nombre(self, nombre):
        return self.bd_mongo.variables.find_one({'nombre':nombre})
