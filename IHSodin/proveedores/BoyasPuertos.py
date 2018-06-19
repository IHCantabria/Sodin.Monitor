# -*- coding: utf-8 -*-

import json
import config as cfg
import requests
from requests.exceptions import HTTPError
from proveedores.configuracion import config_boyas
from proveedores.ProveedorBoyas import ProveedorBoyas
from utiles.Utilidades import Utilidades as util

class BoyasPuertos(ProveedorBoyas):
    """Clase para trabajar con datos procedentes de las boyas de Puertos del Estado"""

    def __init__(self):
        self.cfg_proveedor = config_boyas

    def ultima_medida_de_estacion(self, estacion, variable):
        '''Hace una peticion a la api y obtiene la ultima medida disponible'''
        variable_estacion = util.filtrar_lista(estacion['variables'], 'codigo', variable['codigo'])
        numero_datos = 1 #Pedimos solo el último
        datos_json = self.descargar_json_con_datos(variable_estacion['signal'], numero_datos)
        medida = self.extraer_medida_de_json(estacion['id'], variable['codigo'], datos_json)
        return medida

    def descargar_json_con_datos(self, signal_variable_estacion, numero_datos):
        url_con_parametros = self.componer_url_peticion(signal_variable_estacion, numero_datos)
        return self.hacer_peticion_http(url_con_parametros)

    def componer_url_peticion(self, signal_variable_estacion, numero_datos):
        '''Prepara la url de la peticion a la api con los parametros necesarios'''
        url_con_parametros = '{0}/{1}/{2}'.format(self.cfg_proveedor.URL, signal_variable_estacion, numero_datos)
        return url_con_parametros

    def hacer_peticion_http(self, url_con_parametros):
        '''Lee y devuelve el json de una url'''
        sesion = requests.Session()
        response = sesion.get(url_con_parametros, params=None, verify=False)

        if response.status_code != requests.codes.ok:
            raise HTTPError(u'Error http al pedir el json de la url.')
        if not response.content:
            raise ValueError(u'La petición ha devuelto no ha devuelto datos.')

        return response.content

    def extraer_medida_de_json(self, id_estacion, codigo_variable, datos_json):
        (fecha_utc, valor) = self.leer_json(datos_json)
        nueva_medida = self.crear_medida_boyas(id_estacion, codigo_variable, fecha_utc, valor)
        return nueva_medida

    def leer_json(self, datos_json):
        datos = json.loads(datos_json)
        ultimo_dato = datos['datos'][0]
        if not ultimo_dato:
            raise ValueError(u'No se han podido leer los datos del json devuelto por la api.')

        fecha_utc = util.convertir_cadena_a_fecha(ultimo_dato['fecha'], self.cfg_proveedor.FORMATO_FECHA)
        if not self.cfg_proveedor.ES_UTC:
            fecha_utc = util.convertir_a_utc(fecha_utc, cfg.FORMATO_FECHA)
        return (fecha_utc, ultimo_dato['valor'])
