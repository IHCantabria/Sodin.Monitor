# -*- coding: utf-8 -*-

import os
import requests
import config as cfg
from modelos.Medida import Medida
from utiles.Utilidades import Utilidades as util

# pylint: disable=R0201
class ProveedorSAIH(object):
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

    def destino_descarga(self, ruta_descarga, id_estacion):
        fecha_y_hora = util.fecha_actual_str("%d-%m-%Y_%H_%M")
        nombre_fichero = "{0}_{1}.{2}".format(id_estacion, fecha_y_hora, self.cfg_proveedor.FORMATO_FICHERO_DATOS)        
        if not os.path.exists(ruta_descarga):
            try:
                os.mkdir(ruta_descarga)
            except OSError as oserr:
                raise OSError(u'Error creando carpeta. {0}'.format(oserr.strerror))

        ruta_local = os.path.join(ruta_descarga, nombre_fichero)
        return ruta_local

    def crear_medida_saih(self, id_estacion, codigo_variable, fecha, valor):
        if not valor:
            raise ValueError('El valor de la medida esta vacio')
        try:
            fecha_utc = util.convertir_a_utc(fecha, cfg.FORMATO_FECHA)
            valor_convertido = float(valor)

            return Medida({
                'idEstacion': id_estacion,
                'codigoVariable' : codigo_variable,
                'fecha': util.convertir_fecha_a_cadena(fecha_utc, cfg.FORMATO_FECHA),
                'valor': valor_convertido
                })
        except ValueError as verr:
            raise ValueError('Valores imposibles de convertir. {0}'.format(verr.message))

    def borrar_fichero(self, ruta_fichero):
        try:
            os.remove(ruta_fichero)
        except OSError as oserr:
            raise OSError(u'Error al borrar el fichero. {0}'.format(oserr.strerror))

    def tipo_proveedor(self):
        ''' Retorna el tipo de proveedor (= su clase)'''
        return self.__class__.__name__
