# -*- coding: utf-8 -*-
'''Modulo con variables de configuración específicas para el proveedor de Instagram'''

# CLAVES INSTAGRAM API #
CLIENT_ID = '5fa2ca0d15b34dc1b5cba3c7f28ff02b'
CLIENT_SECRET = '72b44a086b41480aa170f3af4e8865a1'
REDIRECT_URI = 'http://localhost:8081/iCallback'
ACCESS_TOKEN = '5161293029.5fa2ca0.4e4b2a7bb9064309ab750e5ecd336e4f' #11/04/2017

URL_RENOVAR_TOKEN = (u'https://api.instagram.com/oauth/authorize/?client_id=' +
                     '5fa2ca0d15b34dc1b5cba3c7f28ff02b&redirect_uri=http://localhost:8081/iCallback&' +
                     'response_type=token&scope=basic+public_content+comments+likes')

# BÚSQUEDA #
HASHTAGS = ['Inundacion', 'Inundaciones', 'Riada', 'Riadas', 'Desbordamiento', u'Daños']
