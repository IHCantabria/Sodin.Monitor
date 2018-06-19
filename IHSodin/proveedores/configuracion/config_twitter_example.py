# -*- coding: utf-8 -*-
'''Modulo con variables de configuración específicas para el proveedor de Twitter'''

# CLAVES TWITTER API #
APP_KEY = ''
APP_SECRET = ''

# PETICIONES
MAX_TWEETS_PETICION = '100'
NUM_LOTES = 10

# BÚSQUEDA (palabras clave + cuentas oficiales + palabras excluidas = MÁXIMO de 290 caracteres) #
RADIO_BUSQUEDA = '25km' #Max 25km de busqueda para twitter api, aunque por ahora no se usa
PALABRAS_CLAVE_FLUVIAL = ['Inundacion', 'Inundaciones', 'Riada', 'Desbordamiento', 'Heridos', 'Rescate'] 
CUENTAS_OFICIALES = ['@UMEgob', '@061Cantabria', '@CRECantabria', '@112Cantabria', '@112Asturias', '@112_SOSDeiak', '@112Aragon']
PALABRAS_CLAVE_COSTERO = ['Inundacion', 'Inundaciones', 'Temporal', 'Paseo Maritimo', 'Heridos', 'Rescate']
PALABRAS_EXCLUIDAS = ['Aniversario', 'Historia']

# GEOCODING #
BING_API_KEY = ("")
