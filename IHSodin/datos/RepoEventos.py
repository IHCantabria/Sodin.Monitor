# -*- coding: utf-8 -*-

from pymongo.errors import PyMongoError
from bson import ObjectId

class RepoEventos(object):
    '''Clase para gestionar la consulta e insercion de datos de Eventos'''

    def __init__(self, configuracion, cliente_mongo):
        self.cfg = configuracion
        self.bd_mongo = cliente_mongo

    def obtener_tipo_evento(self, codigo):
        return self.bd_mongo.tiposEvento.find_one({'codigo': codigo})

    def obtener_evento(self, id_evento):
        return self.bd_mongo.eventos.find_one({"_id": ObjectId(id_evento)})

    def obtener_eventos_activos(self):
        return list(self.bd_mongo.eventos.find({'activo': True}))

    def obtener_eventos(self):
        return list(self.bd_mongo.eventos.find({}))

    def obtener_eventos_activos_de_tipo(self, cod_tipo):
        return list(self.bd_mongo.eventos.find({'activo': True, 'codigoTipo': cod_tipo}))

    def actualizar_evento(self, evento):
        try:
            return self.bd_mongo.eventos.update_one({"_id": ObjectId(evento['_id'])}, {"$set": evento})
        except PyMongoError as pyerr:
            raise PyMongoError(u'Error actualizando evento en BD (pymongo). {0}'.format(pyerr.message))

    def borrar_evento(self, id_evento):
        try:
            return self.bd_mongo.eventos.remove({"_id": ObjectId(id_evento)})
        except PyMongoError as pyerr:
            raise PyMongoError(u'Error borrando evento de BD (pymongo). {0}'.format(pyerr.message))

    def borrar_eventos_estacion(self, id_estacion, cod_tipo):
        return self.bd_mongo.eventos.remove({'idEstacion':id_estacion, 'codigoTipo':cod_tipo})

    def insertar_evento(self, evento):
        try:
            return self.bd_mongo.eventos.insert_one(evento.to_json_obj())
        except PyMongoError as pyerr:
            raise PyMongoError(u'Error insertando evento en BD (pymongo). {0}'.format(pyerr.message))

    def insertar_medida_en_evento(self, id_evento, medida):
        try:
            return self.bd_mongo.eventos.update_one({"_id": ObjectId(id_evento)},
                                                    {"$push": {"datosConfederaciones": medida.to_json_obj()}})
        except PyMongoError as pyerr:
            raise PyMongoError(u'Error insertando medida en evento(pymongo). {0}'.format(pyerr.message))

    def insertar_medida_boya_en_evento(self, id_evento, medida):
        try:
            return self.bd_mongo.eventos.update_one({"_id": ObjectId(id_evento)},
                                                    {"$push": {"datosPuertos": medida.to_json_obj()}})
        except PyMongoError as pyerr:
            raise PyMongoError(u'Error insertando medida de boya en evento(pymongo). {0}'.format(pyerr.message))

    def insertar_tweets_en_evento(self, id_evento, tweets):
        try:
            return self.bd_mongo.eventos.update_one({'_id': ObjectId(id_evento)}, {"$push": {
                'datosTwitter': {'$each': tweets, '$sort':{'id': -1}}}})
        except PyMongoError as pyerr:
            raise PyMongoError(u'Error insertando tweets en evento(pymongo). {0}'.format(pyerr.message))

    def obtener_post_evento(self, id_evento):
        return self.bd_mongo.postEventos.find_one({"idEvento": id_evento})

    def insertar_post_evento(self, post_evento):
        try:
            return self.bd_mongo.postEventos.insert_one(post_evento.to_json_obj())
        except PyMongoError as pyerr:
            raise PyMongoError(u'Error insertando postevento en BD (pymongo). {0}'.format(pyerr.message))

    def borrar_post_evento(self, id_post_evento):
        try:
            return self.bd_mongo.postEventos.remove({"_id": ObjectId(id_post_evento)})
        except PyMongoError as pyerr:
            raise PyMongoError(u'Error borrando postevento de BD (pymongo). {0}'.format(pyerr.message))