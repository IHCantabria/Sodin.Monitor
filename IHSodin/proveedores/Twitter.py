# -*- coding: utf-8 -*-
import re
import HTMLParser
import geocoder
import requests
import pytz
from datetime import *
from dateutil import parser
from dateutil.relativedelta import *
from requests import exceptions
from BeautifulSoup import BeautifulSoup
from proveedores.configuracion import config_twitter
from twython import Twython
from twython import TwythonAuthError

# pylint: disable=R0201
class Twitter(object):
    """Clase para trabajar con datos obtenidos de Twitter"""

    def __init__(self, cfg, log):
        self.cfg = cfg
        self.log = log
        self.twitter_api = Twitter.autenticar_cuenta(config_twitter.APP_KEY,
                                                     config_twitter.APP_SECRET)

    @staticmethod
    def autenticar_cuenta(app_key, app_secret):
        try:
            twython_obj = Twython(app_key, app_secret, oauth_version=2)
            token = twython_obj.obtain_access_token()
            return Twython(config_twitter.APP_KEY, access_token=token)

        except TwythonAuthError as twerr:
            raise TwythonAuthError(u'Error autenticando cuenta de Twitter. {0}'.format(twerr.message))

    def busqueda_tweets_por_lotes(self, props, numero_lotes):
        '''Devuelve una serie de lotes de tweets posicionados si la consulta encuentra suficientes'''
        tweets = []
        for _ in range(numero_lotes):
            resultados = self.obtener_lote_tweets(props)
            if not resultados:
                continue
            tweets.extend(resultados['statuses'])
            try:
                # Si hay varios lotes, guardar MAX_ID para no recibir
                # duplicados
                props['next_max_id'] = self.obtener_maxid_lote(resultados)
            except KeyError:
                break

        return self.geocodificar_tweets(tweets)

    def obtener_lote_tweets(self, props):
        try:
            if props['next_max_id'] is None: # primer lote
                return self.twitter_api.search(q=props['query'], count=props['max_num_tweets'],
                                               geocode=props['query_geo'], since_id=props['id_ultimo'])

            return self.twitter_api.search(q=props['query'], count=props['max_num_tweets'],
                                           geocode=props['query_geo'], include_entities='true',
                                           since_id=props['id_ultimo'], max_id=props['next_max_id'])
        except Exception as ex:
            self.log.escribir(u'No se han podido buscar tweets, error con la API de twitter. {0}'.format(ex.message), self.log.ERROR)
            return None

    def obtener_maxid_lote(self, res_peticion_twitter):
        try:
            next_resultados_url = res_peticion_twitter['search_metadata']['next_results']
            next_max_id = next_resultados_url.split('max_id=')[1].split('&')[0]
            return next_max_id
        except KeyError as kerr:
            raise KeyError(u'Error obteniendo maxid de peticion a twitter. {0}'.format(kerr.message))

    def geocodificar_tweets(self, tweets):
        tweets_con_geo = []
        for tweet in tweets:
            geo_tweet_ok = self.intentar_geocodificar_tweet(tweet)
            if geo_tweet_ok:
                tweets_con_geo.append(tweet)
        return tweets_con_geo

    def intentar_geocodificar_tweet(self, tweet):
        '''Si se encuentra posición se añade al campo 'coordenadas'. En el campo 'tipo_geo' se incluye
        info de la fuente para el geocoding'''

        if tweet['coordinates'] is not None:
            self.log.escribir(u'Tweet geolocalizado', self.log.DEBUG)
            tweet['tipo_geo'] = "Geolocalized"
            return True

        if tweet['place'] is not None:
            place_fullname = tweet['place']['full_name']
            if place_fullname:
                self.log.escribir(u'Tweet ubicado a partir de Geotag', self.log.DEBUG)
                coords_geojson = self.bing_geocode(place_fullname)
                if coords_geojson is not None:
                    if 'geometry' in coords_geojson:
                        tweet['tipo_geo'] = "Geotagged"
                        tweet['coordinates'] = coords_geojson['geometry']
                        return True

        if tweet['user'] is not None:
            user_location = tweet['user']['location']
            if user_location:
                self.log.escribir(u'Tweet ubicado a partir de posicion del usuario', self.log.DEBUG)
                coords_geojson = self.bing_geocode(user_location)
                if coords_geojson is not None:
                    if 'geometry' in coords_geojson:
                        tweet['tipo_geo'] = "Geouser"
                        tweet['coordinates'] = coords_geojson['geometry']
                        return True

        self.log.escribir(u'Tweet imposible de geolocalizar', self.log.DEBUG)
        return False

    def bing_geocode(self, lugar):
        try:
            geocod = geocoder.bing(lugar, key=config_twitter.BING_API_KEY)
            coordenadas = geocod.geojson
            return coordenadas
        except ValueError as varr:
            self.log.escribir(u'Error de geocoding. Lugar: {0}. {1}'.format(lugar, varr.message),
                              self.log.ERROR)
            return None

    def filtro_avanzado_tweets_evento(self, tweets, evento):        
        # Filtrar tweets en los que los topónimos no estén en mayúscula
        # y que estén dentro del periodo del evento
        tweets_filtrados = []
        fecha_inicio_evento = evento['fechaInicio']
        utc = pytz.timezone(u'UTC')
        loc_fecha_inicio = utc.localize(fecha_inicio_evento)

        for tweet in tweets:
            try: 
                #todo: filtrar tweets duplicados (revisar ids)
                fecha_tweet = parser.parse(tweet['created_at'])
                if any(re.search(r'\s' + toponimo, tweet['text']) for toponimo in evento['toponimos']) and fecha_tweet > loc_fecha_inicio:
                    tweets_filtrados.append(tweet)
            except Exception as ex:
                self.log.escribir(u'Tweet no incluido, no se han podido comparar las fechas ({0})'.format(ex.message), self.log.WARNING)
                continue
        
        return tweets_filtrados    

    @staticmethod
    def crear_query_twitter(toponimos, palabras_clave, palabras_excluidas, cuentas_oficiales):
        query = toponimos + ' '
        
        # Palabra clave
        for index, palabra in enumerate(palabras_clave):
            if index == 0:
                query += palabra
            else:
                query += ' OR ' + palabra
        # Cuentas oficiales
        for cuenta in cuentas_oficiales:
            query += ' OR ' + cuenta

        # Palabras excluidas
        for palabra in palabras_excluidas:
            query += ' -' + palabra        

        # Excluir retweets
        query += " -filter:retweets"               

        return query

    @staticmethod
    def crear_query_geo(lon, lat):
        return '{},{},{}'.format(str(lon), str(lat), config_twitter.RADIO_BUSQUEDA)

    def obtener_url_foto_de_tweet(self, tweet):
        url_imagen = None
        try:
            if self.tiene_foto(tweet):
                url_imagen = tweet['entities']['media'][0]['media_url'] #twimg
            elif self.tiene_foto_externa(tweet):
                url_completa = tweet['entities']['urls'][0]['expanded_url'] #instagram
                url_imagen = self.sacar_link_a_foto_instagram(url_completa)
            return url_imagen
        except exceptions.ConnectionError as conerr:
            raise exceptions.ConnectionError(u'No se ha podido conectar para obtener la url de la foto. {0}'
                                             .format(conerr.message))
        except HTMLParser.HTMLParseError as prserr:
            raise HTMLParser.HTMLParseError(prserr.message)

    def sacar_link_a_foto_instagram(self, url_completa):
        fichero = requests.get(url_completa, params=None, verify=False)
        html_source = fichero.content
        soup = BeautifulSoup(html_source)
        meta_tag = soup.findAll('meta', {'property':'og:image'})
        if not meta_tag:
            raise HTMLParser.HTMLParseError("No se ha podido parsear el html para sacar la url de la foto")
        img_url = meta_tag[0]['content']
        return img_url

    def tiene_foto(self, tweet):
        if 'media' in tweet['entities']:
            media = tweet['entities']['media'][0]
            return media.get('type') == 'photo'
        return False

    def tiene_foto_externa(self, tweet):
        # Por ahora solo fotos de instagram
        if tweet['entities']['urls']:
            url = tweet['entities']['urls'][0]['expanded_url']
            return 'instagram' in url
        return False
