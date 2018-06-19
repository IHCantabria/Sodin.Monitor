# -*- coding: utf-8 -*-

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.errors import ConnectionFailure
from utiles.Utilidades import Utilidades as util
import config as cfg

class RepoUtil(object):
    '''Clase de utilidades para el manejo del repositorio de datos contra MongoDb'''

    @staticmethod
    def inicializar_cliente(uri_mongodb, nombre_bd):
        try:
            return MongoClient(uri_mongodb)[nombre_bd]
        except ConnectionFailure as conerr:
            raise Exception(u'Error conectando a la BD de Mongo. {0}'.format(conerr.message))
        except Exception as operr:
            raise Exception(u'Error autenticando. {0}'.format(operr.message))

    @staticmethod
    def insertar_ejecucion(cliente_mongo, ejecucion_ok, nombre_operacional):
        try:
            fecha_actual = util.fecha_actual(cfg.FORMATO_FECHA)
            ejecucion = {'fecha': fecha_actual, 'estado': ejecucion_ok, 'tipo': nombre_operacional}
            return cliente_mongo.ejecuciones.insert_one(ejecucion)
        except PyMongoError as pyerr:
            raise PyMongoError(u'Error insertando datos de la ejecución en BD (pymongo). {0}'
                               .format(pyerr.message))
