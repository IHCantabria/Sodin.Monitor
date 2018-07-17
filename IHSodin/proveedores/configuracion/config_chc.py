# -*- coding: utf-8 -*-
'''Modulo con las variables de configuración específicas del proveedor  de la CHC'''

# LINKS #
#URL = r'https://www.chcantabrico.es/evolucion-de-niveles/-/descarga/csv/nivel/N020'
URL_NIVEL = r'https://www.chcantabrico.es/evolucion-de-niveles/-/descarga/csv/nivel/'
URL_PRECIPITACION = r'https://www.chcantabrico.es/precipitacion-acumulada/-/descarga/csv/pluvio/'

#URL = (r'https://www.chcantabrico.es/index.php/es/actuaciones/dph/seguimientocontroldph/' +
#       'redescontrolhidrologia/saihchc/saihchc-2/4470-grafico-estacion')
PARAMETROS = ['cod_estacion', 'tipo', 'numerico']

# DATOS #
FORMATO_FICHERO_DATOS = 'csv'
CODIGO_FICHERO_DATOS = 1
FILAS_CABECERA = 2

# DATOS #
FORMATO_FECHA = "%d/%m/%Y %H:%M:%S"

#VARIABLES (hack por cambio en la forma de servir los datos de la CHC!!)
COD_NIVEL = 0
COD_PRECIPITACION = 1

# DETECCION #
VARIABLE_DETECCION = 'Nivel'
NIVEL_ALERTA = 'alerta'
