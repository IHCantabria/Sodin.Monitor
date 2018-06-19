# -*- coding: utf-8 -*-

import requests
import config as cfg
from modelos.Medida import Medida
from utiles.Utilidades import Utilidades as util

# pylint: disable=R0201
class ProveedorBoyas(object):
    '''Clase abstracta que proporciona la estructura y comportamiento común
    entre distintos proveedores de datos de Estaciones SAIH'''

    def hay_conexion(self, tipo_conexion, url):
        if tipo_conexion == 'HTTP':
            try:
                conexion = requests.get(url, verify=False)
                if conexion.status_code == requests.codes.ok:
                    return True
                else:
                    raise IOError
            except IOError as ioerr:
                raise IOError(u'Imposible establecer conexión. {0}'.format(ioerr.strerror))

    def crear_medida_boyas(self, id_estacion, codigo_variable, fecha_utc, valor):
        try:
            valor_convertido = round(float(valor), 2)

            return Medida({
                'idEstacion': id_estacion,
                'codigoVariable' : codigo_variable,
                'fecha': util.convertir_fecha_a_cadena(fecha_utc, cfg.FORMATO_FECHA),
                'valor': valor_convertido
                })
        except ValueError as verr:
            raise ValueError('Valores imposibles de convertir. {0}'.format(verr.message))

    def tipo_proveedor(self):
        ''' Retorna el tipo de proveedor (= su clase)'''
        return self.__class__.__name__
