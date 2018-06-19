# -*- coding: utf-8 -*-
''' Script para usar los Microsoft Cognitive Services.
Viene del proyecto de Github: https://github.com/Microsoft/Cognitive-Vision-Python '''

import time
import requests
import config as cfg

_URL = 'https://westeurope.api.cognitive.microsoft.com/vision/v1.0/analyze'
##'https://westus.api.cognitive.microsoft.com/vision/v1.0/analyze'##
_KEY = cfg.COMPUTER_VISION_API_KEY
_MAX_NUM_RETRIES = 10

def process_request(json, data, headers, params):

    """
    Helper function to process the request to Project Oxford

    Parameters:
    json: Used when processing images from its URL. See API Documentation
    data: Used when processing image read from disk. See API Documentation
    headers: Used to pass the key information and the data type request
    """

    retries = 0
    result = None

    while True:

        response = requests.request('post', _URL, json=json, data=data, headers=headers, params=params)

        if response.status_code == 429:

            print "Message: %s" % (response.json()['error']['message'])

            if retries <= _MAX_NUM_RETRIES:
                time.sleep(1)
                retries += 1
                continue
            else:
                print 'Error: failed after retrying!'
                break

        elif response.status_code == 200 or response.status_code == 201:

            if 'content-length' in response.headers and int(response.headers['content-length']) == 0:
                result = None
            elif 'content-type' in response.headers and isinstance(response.headers['content-type'], str):
                if 'application/json' in response.headers['content-type'].lower():
                    result = response.json() if response.content else None
                elif 'image' in response.headers['content-type'].lower():
                    result = response.content
        else:
            raise Exception(u'Error del servicio de analisis de imagen de Microsoft. Codigo:{0}. Descripcion:{1}'
                            .format(response.status_code, response.json()['error']['message']))

        break
    return result
