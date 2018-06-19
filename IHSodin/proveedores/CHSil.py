# -*- coding: utf-8 -*-

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.exceptions import HTTPError
from proveedores.ProveedorSAIH import ProveedorSAIH
from proveedores.configuracion import config_chsil
from BeautifulSoup import BeautifulSoup
from utiles.Utilidades import Utilidades as util

class CHSil(ProveedorSAIH):
    """Clase para trabajar con datos procedentes de las estaciones SAIH
    de la Confederación Hidrográfica Miño-Sil"""

    def __init__(self):
        self.cfg_proveedor = config_chsil

        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def ultima_medida_de_estacion(self, estacion, variable):
        '''Descarga el fichero con el ultimo lote de datos de una variable
        y extrae la ultima medida disponible'''
        variable_estacion = util.filtrar_lista(estacion['variables'], 'codigo', variable['codigo'])
        html = self.descargar_html_con_datos(variable_estacion['signal'])
        medida = self.extraer_medida_de_html(estacion['id'], variable['codigo'], html)
        return medida

    def descargar_html_con_datos(self, signal_variable_estacion):
        parametros_peticion = self.crear_parametros_peticion(signal_variable_estacion)
        return self.hacer_peticion_http(parametros_peticion)

    def crear_parametros_peticion(self, signal_variable_estacion):
        '''Prepara la peticion componiendo un objeto con los parametros necesarios'''
        param_url = '/datos/excel/tag:{0}'.format(signal_variable_estacion)
        parametros = {
            self.cfg_proveedor.PARAMETROS[0]: param_url,
            self.cfg_proveedor.PARAMETROS[1]: 0
            }
        return parametros

    def hacer_peticion_http(self, parametros_peticion):
        '''Lee y devuelve el codigo html de una url'''
        sesion = requests.Session()
        #Para autenticar la cookie,llamada a la url base en la primera peticion
        sesion.post(self.cfg_proveedor.URL)
        response = sesion.get(self.cfg_proveedor.URL, params=parametros_peticion, verify=False)

        if response.status_code != requests.codes.ok:
            raise HTTPError(u'Error http al pedir el html de la url.')
        if not response.content:
            raise ValueError(u'La petición ha devuelto una cadena vacía.')

        return response.content

    def extraer_medida_de_html(self, id_estacion, codigo_variable, html):
        (fecha, valor) = self.leer_html(html)
        nueva_medida = self.crear_medida_saih(id_estacion, codigo_variable, fecha, valor)
        return nueva_medida

    def leer_html(self, html):
        soup = BeautifulSoup(html)
        tablas = soup.findAll("table", attrs={"class":"tabla"})
        body = tablas[1].find('tbody') # Los datos están en la segunda tabla
        filas = body.findAll('tr')
        for fila in filas[1:2]: #Saltar la cabecera y recorrer solo la primera linea
            cols = fila.findAll('td', attrs={"class":"celdal"})
            fecha = cols[0].text.strip()
            valor = cols[1].text.strip()
        return self._adaptar_datos(fecha, valor)

    # pylint: disable=R0201
    def _adaptar_datos(self, fecha, valor):
        fecha = fecha.replace('/', '-')
        valor = valor.replace(',', '.')
        return (fecha, valor)
