# -*- coding: utf-8 -*-
''' Script para usar el servicio de an?lisis sem?ntico de Microsoft Cognitive Services.
Viene del ejemplo : https://text-analytics-demo.azurewebsites.net/Home/SampleCode '''

import json
import config as cfg
import requests

_URL = 'https://westus.api.cognitive.microsoft.com/'
_KEY = cfg.TEXT_API_KEY
_HEADERS = {'Content-Type':'application/json', 'Ocp-Apim-Subscription-Key':_KEY}
_NUM_DETECT_LANGS = 1
_QUOTA_EXCEEDED_CODE = 403

def analisis_texto(id_tweet, texto):    
    # Detectar idioma del texto
    params_idioma = {"documents": [{"id": str(id_tweet), "text": texto}]}
    idioma = detectar_idioma(params_idioma)

    # Sacar palabras clave del texto
    parametros = {"documents": [{"id": str('id'), "language": idioma['iso6391Name'], "text": texto}]}
    palabras_clave = detectar_palabras_clave(parametros)

    # Obtener sentimiento del texto
    sentimiento = detectar_sentimiento(parametros)

    return (palabras_clave['keyPhrases'], sentimiento['score'])    

def detectar_idioma(params):
    language_detection_url = _URL + 'text/analytics/v2.0/languages'

    response = requests.request('post', language_detection_url, data=json.dumps(params), headers=_HEADERS)
    if response.status_code == _QUOTA_EXCEEDED_CODE:
        raise Exception(u'Detección de idioma - {0}'.format(obj['message']))
    result = response.content    
    obj = json.loads(result)    
    return obj['documents'][0]['detectedLanguages'][0]

def detectar_palabras_clave(params):
    batch_keyphrase_url = _URL + 'text/analytics/v2.0/keyPhrases'
    response = requests.request('post', batch_keyphrase_url, data=json.dumps(params), headers=_HEADERS)
    if response.status_code == _QUOTA_EXCEEDED_CODE:
        raise Exception(u'Detección de palabras clave - {0}'.format(obj['message']))

    result = response.content
    obj = json.loads(result)    
    return obj['documents'][0]

def detectar_sentimiento(params):
    batch_sentiment_url = _URL + 'text/analytics/v2.0/sentiment'
    response = requests.request('post', batch_sentiment_url, data=json.dumps(params), headers=_HEADERS)
    if response.status_code == _QUOTA_EXCEEDED_CODE:
        raise Exception(u'Detección de sentimiento - {0}'.format(obj['message']))

    result = response.content
    obj = json.loads(result)    
    return obj['documents'][0]
