# -*- coding: utf-8 -*-
import json
from utiles.Utilidades import Utilidades as util
import config

class Conversor(object):
    """Clase que convierte clases customizadas en objetos json"""

    def to_json_obj(self):
        '''Convierte la clase a un objeto de python'''
        json_str = self.to_json_str()
        try:
            python_obj = json.loads(json_str, object_hook=Conversor.datetime_parser)
            return python_obj
        except ValueError as verr:
            raise ValueError(u'Error convirtiendo a objeto python. {0}'.format(verr.message))

    def to_json_str(self):
        '''Devuelve la clase como un string de json'''
        try:
            json_str = json.dumps(self, default=Conversor.json_default)
            return json_str
        except ValueError as verr:
            raise ValueError(u'Error parseando valores a json. {0}'.format(verr.message))
        except AttributeError as atterr:
            raise AttributeError(u'Error parseando atributo a json. {0}'.format(atterr.message))

    @staticmethod
    def json_default(clase):
        return clase.__dict__

    @staticmethod
    def datetime_parser(json_dict):
        '''Se busca cualquier campo con fechas para convertir a datetime'''
        for (key, value) in json_dict.items():
            if isinstance(value, basestring):
                try:
                    json_dict[key] = util.convertir_cadena_a_fecha(value, config.FORMATO_FECHA)
                except (ValueError, AttributeError):
                    pass
        return json_dict
