# -*- coding: utf-8 -*-
'''Modulo con las variables de configuración específicas del proveedor  de la CH del Ebro'''

# LINKS #
URL = r'http://saihebro.com/saihebro/api.php'
 #Ejemplo http://saihebro.com/saihebro/api.php?senal=A059H17NRIO1&apikey=yourapikey
APIKEY = ''
PARAMETROS = ['senal', 'apikey']

# DATOS #
FORMATO_FECHA = "%d/%m/%Y %H:%M"

# DETECCION #
VARIABLE_DETECCION = 'Caudal'
NIVEL_ALERTA = 'prealerta'
