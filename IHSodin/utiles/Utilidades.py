# -*- coding: utf-8 -*-

import os
import urllib
from datetime import datetime
import config as cfg
from BeautifulSoup import BeautifulSoup

class Utilidades(object):
    """Clase con utilidades generales"""

    @staticmethod
    def filtrar_lista(lista, campo, valor):
        '''Devuelve el primer elemento de una lista que cumple la condicion'''
        lista_filtrada = [x for x in lista if x[campo] == valor]
        if lista_filtrada:
            return lista_filtrada[0]
        return None

    @staticmethod
    def existe_elemento(lista, elemento):
        if elemento in lista:
            return True
        return False

    @staticmethod
    def cambiar_formato_fecha(cadena_fecha, formato_inicial):
        try:
            fecha = datetime.strptime(cadena_fecha, formato_inicial)
            return datetime.strftime(fecha, cfg.FORMATO_FECHA)
        except ValueError as verr:
            raise ValueError('Cambio de formato imposible. {0}'.format(verr.message))

    @staticmethod
    def convertir_cadena_a_fecha(cadena_fecha, formato):
        try:
            return datetime.strptime(cadena_fecha, formato)
        except ValueError as verr:
            raise ValueError('Cadena no parseable a fecha. {0}'.format(verr.message))

    @staticmethod
    def convertir_fecha_a_cadena(fecha, formato):
        try:
            return fecha.strftime(formato)
        except ValueError as verr:
            raise ValueError('Error parseando fecha a cadena. {0}'.format(verr.message))

    @staticmethod
    def convertir_a_utc(cadena_fecha_local, formato):
        fecha_local = Utilidades.convertir_cadena_a_fecha(cadena_fecha_local, formato)
        utc_offset_timedelta = datetime.utcnow() - datetime.now()
        return fecha_local + utc_offset_timedelta

    @staticmethod
    def fecha_actual(formato):
        '''Devuelve un objeto fecha en con la hora actual en UTC'''
        fecha_utc_str = datetime.utcnow().__format__(formato)
        fecha_utc = Utilidades.convertir_cadena_a_fecha(fecha_utc_str, formato)
        return fecha_utc

    @staticmethod
    def fecha_actual_str(formato):
        '''Devuelve un string con la hora actual en UTC'''
        fecha_utc_str = datetime.utcnow().__format__(formato)
        return fecha_utc_str

    @staticmethod
    def descarga_foto_instagram(url_foto):
        fichero = urllib.urlopen(url_foto)
        html_source = fichero.read()
        soup = BeautifulSoup(html_source)
        meta_tag = soup.findAll('meta', {'property':'og:image'})
        img_url = meta_tag[0]['content']

        nombre_fichero = "{0}_{1}.{2}".format('foto', Utilidades.fecha_actual_str("%d-%m-%Y_%H_%M"), 'jpg')
        ruta_descarga = os.path.join(cfg.RUTA_BASE_EJECUCIONES, cfg.CARPETA_DESCARGAS, nombre_fichero)

        urllib.urlretrieve(img_url, ruta_descarga)
        return ruta_descarga
