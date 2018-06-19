# -*- coding: utf-8 -*-

import os
import csv
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from proveedores.configuracion import config_chc
from proveedores.ProveedorSAIH import ProveedorSAIH

class CHCantabrico(ProveedorSAIH):
    """Clase para trabajar con datos procedentes de las estaciones SAI de la CHC"""

    def __init__(self, cfg):
        self.cfg_proveedor = config_chc
        self.cfg = cfg
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def ultima_medida_de_estacion(self, estacion, variable):
        '''Descarga el fichero con el ultimo lote de datos de una variable
        y extrae la ultima medida disponible'''
        fichero_descargado = self.descargar_csv_con_variable(estacion['id'], variable['codigo'])
        medida = self.extraer_medida_de_csv(estacion['id'], variable['codigo'], fichero_descargado)
        self.borrar_fichero(fichero_descargado)
        return medida

    def descargar_csv_con_variable(self, id_estacion, cod_variable):
        (parametros_peticion, ruta_local) = self.preparar_descarga(id_estacion, cod_variable)
        return self.descarga_csv(parametros_peticion, ruta_local)

    def preparar_descarga(self, id_estacion, cod_variable):
        '''Compone los parametros de la peticion y la ruta de destino y devuelve una tupla con ambos'''
        parametros = self.crear_parametros_peticion(id_estacion, cod_variable)
        ruta_compuesta = os.path.join(self.cfg.RUTA_BASE_EJECUCIONES, self.cfg.CARPETA_DESCARGAS, self.tipo_proveedor())
        ruta_local = self.destino_descarga(ruta_compuesta, id_estacion)
        return (parametros, ruta_local)

    def crear_parametros_peticion(self, id_estacion, cod_variable):
        '''Prepara la peticion componiendo un objecto con los parametros dinámicos'''
        parametros = {
            self.cfg_proveedor.PARAMETROS[0]: id_estacion,
            self.cfg_proveedor.PARAMETROS[1]: cod_variable,
            self.cfg_proveedor.PARAMETROS[2]: self.cfg_proveedor.CODIGO_FICHERO_DATOS
            }
        return parametros

    def descarga_csv(self, parametros_peticion, destino):
        '''Descarga el fichero csv desde un origen externo a un destino local'''
        try:
            csv_datos = requests.get(self.cfg_proveedor.URL, params=parametros_peticion, verify=False)
            if not csv_datos.content:
                raise ValueError(u'La petición ha devuelto una cadena vacía.')

            with open(destino, 'w') as fichero:
                fichero.write(csv_datos.content)
            return destino
        except IOError as ioerr:
            raise IOError(u'Error al escribir el fichero en disco. {0}'.format(ioerr.strerror))

    def extraer_medida_de_csv(self, id_estacion, codigo_variable, ruta_fichero):
        try:
            with open(ruta_fichero, 'rb') as fichero:
                lector = csv.reader(fichero, delimiter=';')
                fila_ultima_medida = self.leer_csv(lector)
                nueva_medida = self.crear_medida_saih(id_estacion, codigo_variable, fila_ultima_medida[0],
                                                      fila_ultima_medida[1])
                fichero.close()
            return nueva_medida
        except IOError:
            raise IOError('Error leyendo fichero csv')

    def leer_csv(self, lector):
        for _ in range(self.cfg_proveedor.FILAS_CABECERA): #Saltar las filas de la cabecera
            next(lector)
        fila_ultima_medida = next(lector)
        return fila_ultima_medida
