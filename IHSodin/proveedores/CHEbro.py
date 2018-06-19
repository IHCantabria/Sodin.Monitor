# -*- coding: utf-8 -*-
import json
import requests
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.exceptions import HTTPError
from proveedores.ProveedorSAIH import ProveedorSAIH
from proveedores.configuracion import config_chebro
from utiles.Utilidades import Utilidades as util

class CHEbro(ProveedorSAIH):
    """Clase para trabajar con datos procedentes de las estaciones SAIH
    de la Confederación Hidrográfica Miño-Sil"""

    def __init__(self):
        self.cfg_proveedor = config_chebro

        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def ultima_medida_de_estacion(self, estacion, variable):
        '''Hace una peticion a la api y obtiene la ultima medida disponible'''
        variable_estacion = util.filtrar_lista(estacion['variables'], 'codigo', variable['codigo'])
        datos_json = self.descargar_json_con_datos(variable_estacion['signal'])
        medida = self.extraer_medida_de_json(estacion['id'], variable['codigo'], datos_json)
        return medida

    def descargar_json_con_datos(self, signal_variable_estacion):
        parametros_peticion = self.crear_parametros_peticion(signal_variable_estacion)
        return self.hacer_peticion_http(parametros_peticion)

    def crear_parametros_peticion(self, signal_variable_estacion):
        '''Prepara la peticion componiendo un objeto con los parametros necesarios'''
        parametros = {
            self.cfg_proveedor.PARAMETROS[0]: signal_variable_estacion,
            self.cfg_proveedor.PARAMETROS[1]: self.cfg_proveedor.APIKEY
            }
        return parametros

    def hacer_peticion_http(self, parametros_peticion):
        '''Lee y devuelve el json de una url'''
        sesion = requests.Session()
        # Aplicar retardo para evitar superar el limite de peticiones de la API de CHEBRO (max 50/min)
        time.sleep(2.0)
        response = sesion.get(self.cfg_proveedor.URL, params=parametros_peticion, verify=False)

        if response.status_code != requests.codes.ok:
            raise HTTPError(u'Error http al pedir el json de la url.')
        if not response.content:
            raise ValueError(u'La petición no ha devuelto datos.')
        if  u'Api key' in response.content.decode('latin-1'): #hack para poder leer el error que devuelve la api cuando se supera el limite
            raise HTTPError(u'Error de acceso al API. {0}'.format(response.content.decode('latin-1')))

        return response.content

    def extraer_medida_de_json(self, id_estacion, codigo_variable, datos_json):
        (fecha, valor) = self.leer_json(datos_json)
        nueva_medida = self.crear_medida_saih(id_estacion, codigo_variable, fecha, valor)
        return nueva_medida

    def leer_json(self, datos_json):
        datos = json.loads(datos_json)
        return self._adaptar_datos(datos['fecha'], datos['valor'])

    def _adaptar_datos(self, fecha, valor):
        fecha = fecha.replace('/', '-')
        valor = valor.replace(',', '.')
        return (fecha, valor)
