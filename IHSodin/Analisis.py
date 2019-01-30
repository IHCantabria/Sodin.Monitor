# -*- coding: utf-8 -*-
import re
from utiles.Utilidades import Utilidades as util
from servicios_ia import computer_vision as cpu_vision
from servicios_ia import text_analytics
from proveedores.Twitter import Twitter
from datos.RepoEventos import RepoEventos
from datos.RepoEstaciones import RepoEstaciones
from datos.RepoUtil import RepoUtil as repo
from modelos.PostEvento import PostEvento

class Analisis(object):
    """Clase encargada del analisis y postproceso de un evento de inundación"""

    def __init__(self, cfg, log):
        self.cfg = cfg
        self.log = log
        self.twitter = Twitter(self.cfg, self.log)
        self.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        self.repo_estaciones = RepoEstaciones(cfg, self.cliente_mongo)
        self.repo_eventos = RepoEventos(cfg, self.cliente_mongo)
        self.tipo_json = 'json'
        self.tipo_binario = 'octet-stream'
        self.campos_analisis_foto = 'Categories, Tags, Description, Faces, ImageType, Adult'

    def post_proceso_de_evento(self, evento):
        '''Analiza las fotos y textos, procesa las medidas de los sensores,
        extrae estadisticas y metadatos y guarda todo en un objeto PostEvento en la BD'''

        # Analisis ia de fotos y textos de los tweets
        self.log.escribir(u'2) Procesar tweets', self.log.INFO)
        tweets_post_procesados = self.analisis_tweets(evento['datosTwitter'])

        # Analizar datos del medio
        self.log.escribir(u'3) Procesar medidas de sensores', self.log.INFO)
        medidas_in_situ = evento['datosConfederaciones'] + evento['datosPuertos']
        medidas_post_procesadas = self.procesar_medidas(medidas_in_situ)

        # Guardar PostEvento en BD
        self.log.escribir(u'4) Insertar PostEvento en BD', self.log.INFO)
        post_evento = self.crear_post_evento(evento, tweets_post_procesados, medidas_post_procesadas)
        repo_eventos = RepoEventos(self.cfg, self.cliente_mongo)
        return repo_eventos.insertar_post_evento(post_evento)    

    def analisis_tweets(self, tweets):
        tweets_postevento = []
        for tweet in tweets:
            try:
                tweets_postevento.append(self.procesar_tweet(tweet))
            except Exception as ex:
                self.log.escribir(u'Se ha producido un error analizando el tweet. {0}'.format(ex.message),
                                  self.log.WARNING)
                continue
        return tweets_postevento

    def procesar_tweet(self, tweet):
        self.log.escribir(u'   Analizar tweet:', self.log.INFO)
        foto_procesada = self.analizar_foto_del_tweet(tweet)
        texto_procesado = self.analizar_texto_del_tweet(tweet)
        metadatos = self.extraer_metadatos_del_tweet(tweet)
        tweet_postevento = {'id_tweet': str(tweet['id']), 'metadatos' : metadatos, 'datos_foto' : foto_procesada,
                            'datos_texto' : texto_procesado}
        return tweet_postevento

    def analizar_foto_del_tweet(self, tweet):
        self.log.escribir(u'   - Buscar fotos asociadas', self.log.INFO)
        try:
            foto = None
            url_foto = self.twitter.obtener_url_foto_de_tweet(tweet)
            if url_foto is not None:
                self.log.escribir(u'      Ejecución de análisis i.a. de la foto', self.log.INFO)
                datos_analisis = self.analizar_foto_externa(self.campos_analisis_foto, url_foto)
                foto = self.crear_objeto_foto(self.campos_analisis_foto, datos_analisis, url_foto)
            else:
                self.log.escribir(u'      Tweet sin foto asociada', self.log.INFO)
        except Exception as ex:
            self.log.escribir(u'No se ha podido hacer el análisis de imagen. {0}'.format(ex.message), self.log.WARNING)
        finally:
            return foto

    def analizar_foto_externa(self, campos_busqueda, url_foto):
        (cabeceras, parametros) = self.config_peticion_api_vision(campos_busqueda, self.tipo_json)
        datos_analisis = cpu_vision.process_request({'url': url_foto}, None, cabeceras, parametros)
        return datos_analisis

    def analizar_foto_en_disco(self, campos_busqueda, ruta_en_disco):
        with open(ruta_en_disco, 'rb') as fichero:
            datos = fichero.read()
        (cabeceras, parametros) = self.config_peticion_api_vision(campos_busqueda, self.tipo_binario)
        datos_analisis = cpu_vision.process_request(None, datos, cabeceras, parametros)
        return datos_analisis

    def config_peticion_api_vision(self, campos_busqueda, tipo):
        '''Genera las cabeceras y parametros necesarios para la peticion a la api'''
        cabeceras = dict()
        cabeceras['Ocp-Apim-Subscription-Key'] = self.cfg.COMPUTER_VISION_API_KEY
        cabeceras['Content-Type'] = 'application/{0}'.format(tipo)

        parametros = {'visualFeatures': campos_busqueda, 'language':'en', 'details': 'Landmarks'}
        return (cabeceras, parametros)

    # pylint: disable=R0201
    def crear_objeto_foto(self, campos, datos_analisis, url_foto):
        foto_procesada = {}
        for campo in campos.replace(' ', '').split(','):
            campo_camelcase = campo[:1].lower() + campo[1:]
            foto_procesada[campo] = datos_analisis[campo_camelcase]
        # Añadir la url original de la foto
        foto_procesada['url'] = url_foto
        return foto_procesada

    def analizar_texto_del_tweet(self, tweet):
        try:
            self.log.escribir(u'   - Análisis semántico del texto', self.log.INFO)
            (palabras_clave, sentimiento) = text_analytics.analisis_texto(tweet['id'], tweet['text'])
            texto_procesado = {'texto': tweet['text'], 'palabras_clave': palabras_clave, 'sentimiento': sentimiento}            
        except Exception as ex:
            self.log.escribir(u'No se ha podido hacer el análisis del texto. {0}'.format(ex.message), self.log.WARNING)
            texto_procesado = {'texto': tweet['text'], 'palabras_clave': [], 'sentimiento': 1}
        finally:
            return texto_procesado

    def extraer_metadatos_del_tweet(self, tweet):
        self.log.escribir(u'   - Extracción de metadatos del tweet', self.log.INFO)
        return {
            'coordenadas': tweet.get('coordinates'),
            'hashtags': tweet.get('entities').get('hashtags', []),
            'n_retweets': tweet.get('retweet_count', 0),
            'n_likes': tweet.get('favorite_count', 0),            
            #'sensible': tweet['possibly_sensitive'],
            'fecha_creacion': tweet.get('created_at'),
            'verified': tweet.get('user').get('verified'),
            'account': tweet.get('user').get('screen_name')
            #todo: guardar si tiene enlaces o no. links:true
            }

    def procesar_medidas(self, medidas):
        '''Estandarizacion de los datos de los sensores'''
        self.log.escribir(u'   - Estandarización de datos', self.log.INFO)
        # Pasar las fechas internas de las medidas a cadena para poder insertar
        # en BD
        for medida in medidas:
            medida['fecha'] = util.convertir_fecha_a_cadena(medida['fecha'], self.cfg.FORMATO_FECHA)
        return medidas

    def crear_post_evento(self, evento, tweets_procesados, medidas_procesadas):
        tipo = self.repo_eventos.obtener_tipo_evento(evento['codigoTipo'])
        estacion = self.repo_estaciones.obtener_estacion(evento['idEstacion'])

        try:
            nuevo_post_evento = PostEvento({
                'idEvento' : str(evento['_id']),
                'tipo': tipo['nombre'],
                'lugar': estacion['nombre'],
                'idEstacion': evento['idEstacion'],
                'coords': estacion['coordenadas'],
                'medidas': medidas_procesadas,
                'tweets': tweets_procesados,
                'fechaInicio': util.convertir_fecha_a_cadena(evento['fechaInicio'], self.cfg.FORMATO_FECHA),
                'fechaFin': util.convertir_fecha_a_cadena(evento['fechaFin'], self.cfg.FORMATO_FECHA)
                })
            return nuevo_post_evento
        except AttributeError as aterr:
            raise AttributeError(u'Error creando post evento. {0}'.format(aterr.message))
