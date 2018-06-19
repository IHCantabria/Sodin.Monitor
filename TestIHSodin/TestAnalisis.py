# -*- coding: utf-8 -*-
import unittest
import os
import re
import config_tests as cfg
from utiles.Utilidades import Utilidades as util
from servicios_ia import text_analytics
from Analisis import Analisis
from LogSodin import LogSodin
from datos.RepoUtil import RepoUtil as repo
from datos.RepoEventos import RepoEventos
from datos.RepoTiposEvento import RepoTiposEvento
from datos.RepoEstaciones import RepoEstaciones
from proveedores.Twitter import Twitter
from bson import ObjectId

class Test_Analisis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.log = LogSodin(cfg, cfg.FICHERO_LOG_GESTOR, LogSodin.LOGGER_MONITOR)
        cls.log.configurar_log()
        cls.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        cls.repo_eventos = RepoEventos(cfg, cls.cliente_mongo)
        cls.repo_tipos_evento = RepoTiposEvento(cfg, cls.cliente_mongo)
        cls.repo_estaciones = RepoEstaciones(cfg, cls.cliente_mongo)
        cls.analisis = Analisis(cfg, cls.log)
        cls.twitter = Twitter(cfg, cls.log)

    def test_analiza_foto_externa(self):
        url_foto_test = 'https://oxfordportal.blob.core.windows.net/vision/Analysis/3.jpg'
        datos_analisis = self.analisis.analizar_foto_externa(self.analisis.campos_analisis_foto, url_foto_test)
        self.assertIsNotNone(datos_analisis)
        self.assertTrue(datos_analisis.has_key('description'))
        self.assertTrue(datos_analisis.has_key('tags'))
        self.assertTrue(datos_analisis.has_key('categories'))

    def test_analiza_foto_en_disco(self):
        nombre_fichero = 'test_foto1.jpg'
        ruta_local_foto = os.path.join(cfg.RUTA_BASE_EJECUCIONES, nombre_fichero)
        datos_analisis = self.analisis.analizar_foto_en_disco('Categories, Tags, Description', ruta_local_foto)
        self.assertIsNotNone(datos_analisis)
        self.assertTrue(datos_analisis.has_key('description'))
        self.assertTrue(datos_analisis.has_key('tags'))
        self.assertTrue(datos_analisis.has_key('categories'))

    def test_analiza_imagen_tweet_con_foto(self):
        tweet_fake = {'entities':{'media':[{'media_url':'http://pbs.twimg.com/media/C_EAZ4kXsAAv6xx.jpg',
                                            'type': 'photo'}]}}
        foto = self.analisis.analizar_foto_del_tweet(tweet_fake)
        self.assertIsNotNone(foto)

    def test_analiza_imagen_tweet_con_foto_externa(self):
        tweet_fake = {'entities':{'urls':[{'expanded_url':'https://www.instagram.com/p/BCYyzbkssMD/'}]}}
        foto = self.analisis.analizar_foto_del_tweet(tweet_fake)
        self.assertIsNotNone(foto)

    def test_proceso_completo_de_tweet(self):
        query = Twitter.crear_query_twitter('Inundacion OR Lluvia filter:twimg', '', '', '')
        props = {'query': query, 'query_geo': '', 'id_ultimo': 0, 'next_max_id': None, 'max_num_tweets': 1}
        resultados = self.twitter.obtener_lote_tweets(props)
        tweet = resultados['statuses'][0]

        tweet = self.analisis.procesar_tweet(tweet)
        self.assertTrue(tweet.has_key('metadatos'))
        self.assertTrue(tweet.has_key('datos_foto'))
        self.assertTrue(tweet.has_key('datos_texto'))

    def test_detecta_idioma_de_tweet(self):
        idioma_test = 'es'
        query = Twitter.crear_query_twitter('Inundacion lang:{0}'.format(idioma_test), '', '', '')
        props = {'query': query, 'query_geo': '', 'id_ultimo': 0, 'next_max_id': None, 'max_num_tweets': 1}
        resultados = self.twitter.obtener_lote_tweets(props)
        tweet = resultados['statuses'][0]
        params_json = {
            "documents": [{
                "id": str(tweet['id']),
                "text": tweet['text']
                }]
            }
        idioma = text_analytics.detectar_idioma(params_json)
        self.assertTrue(idioma['iso6391Name'] == idioma_test)

    def test_detecta_palabras_clave_de_tweet(self):
        query = Twitter.crear_query_twitter('Inundacion', '', '', '')
        props = {'query': query, 'query_geo': '', 'id_ultimo': 0, 'next_max_id': None, 'max_num_tweets': 1}
        resultados = self.twitter.obtener_lote_tweets(props)
        tweet = resultados['statuses'][0]
        params_json = {
            "documents": [{
                "id": str(tweet['id']),
                "language": 'es',
                "text": tweet['text']
                }]
            }
        palabras_clave_obj = text_analytics.detectar_palabras_clave(params_json)
        self.assertGreater(palabras_clave_obj['keyPhrases'], 1,
                           "No se ha obtenido ninguna palabra clave del analisis del texto")

    def test_detecta_sentimiento_de_tweet(self):
        query = Twitter.crear_query_twitter('Inundacion :(', '', '', '')
        props = {'query': query, 'query_geo': '', 'id_ultimo': 0, 'next_max_id': None, 'max_num_tweets': 1}
        resultados = self.twitter.obtener_lote_tweets(props)
        tweet = resultados['statuses'][0]
        params_json = {
            "documents": [{
                "id": str(tweet['id']),
                "language": 'es',
                "text": tweet['text']
                }]
            }
        sentimiento_obj = text_analytics.detectar_sentimiento(params_json)
        self.assertLess(sentimiento_obj['score'], 0.75)

    def test_analiza_texto_de_tweet(self):
        query = Twitter.crear_query_twitter('Inundacion', '', '', '')
        props = {'query': query, 'query_geo': '', 'id_ultimo': 0, 'next_max_id': None, 'max_num_tweets': 1}
        resultados = self.twitter.obtener_lote_tweets(props)
        tweet = resultados['statuses'][0]

        texto_procesado = self.analisis.analizar_texto_del_tweet(tweet)
        self.assertIsNotNone(texto_procesado['texto'] and len(texto_procesado['texto']) > 0)
        self.assertGreater(texto_procesado['palabras_clave'], 1,
                           "No se han obtenido palabras clave del analisis del texto")
        self.assertTrue(isinstance(texto_procesado['sentimiento'], float))

    def test_analisis_completo_lote_de_tweets(self):
        query = Twitter.crear_query_twitter('Inundacion filter:twimg', '', '', '')
        props = {'query': query, 'query_geo': '', 'id_ultimo': 0, 'next_max_id': None, 'max_num_tweets': 3}
        resultados = self.twitter.obtener_lote_tweets(props)
        tweets = resultados['statuses']
        tweets_post_procesados = self.analisis.analisis_tweets(tweets)

        self.assertGreater(tweets_post_procesados, 0)
        for tweet in tweets_post_procesados:
            self.assertTrue(tweet.has_key('metadatos'))
            self.assertTrue(tweet.has_key('datos_foto'))
            self.assertTrue(tweet.has_key('datos_texto'))               

    def test_prueba_reg_exp_filtro_tweets(self):
        toponimo_saja = 'Saja'
        toponimo_nansa = 'Nansa'
        lista_toponimos = [toponimo_saja, toponimo_nansa]
        textos = [u'Inundación en el río Saja.', u'Inundación en el río saja.',
                  u'Riada en la desembocadura del Saja', u'Daños por inundaciones en el Nansa']
        lista_saja = []
        lista_nansa = []
        lista_todo = []
        for texto in textos:
            if re.search(u'\s' + toponimo_saja, texto) is not None:
                lista_saja.append(texto)
            if re.search(u'\s' + toponimo_nansa, texto) is not None:
                lista_nansa.append(texto)
            if any(re.search(u'\s' + toponimo, texto) for toponimo in lista_toponimos):
                lista_todo.append(texto)

        self.assertTrue(len(lista_saja), 2)
        self.assertTrue(len(lista_nansa), 1)
        self.assertTrue(len(lista_todo), 3)

if __name__ == '__main__':
    unittest.main()
