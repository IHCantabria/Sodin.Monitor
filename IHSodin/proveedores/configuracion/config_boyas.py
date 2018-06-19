# -*- coding: utf-8 -*-
'''Modulo con las variables de configuración específicas del proveedor de las boyas de Puertos del Estado'''

# LINKS #
URL = r'http://trlplusservicioweb.ihcantabria.com/api/boya/obtenerdatosvariableboya/'
 #Ejemplo http://trlplusservicioweb.ihcantabria.com/api/boya/obtenerdatosvariableboya/[codigoBoya]/[codigoVariable]/[numDatos]
 #http://trlplusservicioweb.ihcantabria.com/api/boya/obtenerdatosvariableboya/3/16/1

# DATOS #
FORMATO_FECHA = "%Y-%m-%dT%H:%M:%S"
ES_UTC = True

# DETECCION #
VARIABLE_DETECCION = 'HMax'
NIVEL_ALERTA = 'alerta'
