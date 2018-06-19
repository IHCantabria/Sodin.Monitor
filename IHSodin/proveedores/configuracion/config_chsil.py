# -*- coding: utf-8 -*-
'''Modulo con las variables de configuración específicas del proveedor  de la CH del Miño-Sil'''

# LINKS #
URL = r'http://saih.chminosil.es/index.php'
 #Ejemplo http://saih.chminosil.es/index.php?url=/datos/excel/tag:A004_AINRIO1&historia=0
PARAMETROS = ['url', 'historia']

# DATOS #
FORMATO_FICHERO_DATOS = 'xls'
CELDA_FECHA = 'A7'
CELDA_VALOR = 'B7'

# DETECCION #
VARIABLE_DETECCION = 'Nivel'
NIVEL_ALERTA = 'alerta'
