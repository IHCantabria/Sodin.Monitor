# -*- coding: utf-8 -*-
import unittest
import HTMLParser
import random
from collections import Counter
import config_tests as cfg
import requests
import re
from utiles.Utilidades import Utilidades as util
from requests.exceptions import ConnectionError
from datos.RepoUtil import RepoUtil as repo
from datos.RepoNucleos import RepoNucleos
from datos.RepoEventos import RepoEventos
from datos.RepoEstaciones import RepoEstaciones
from datos.RepoTiposEvento import RepoTiposEvento
from datos.RepoConfederaciones import RepoConfederaciones
from CoordinadorEvento import CoordinadorEvento
from Gestion import Gestion
from proveedores.Twitter import Twitter
from proveedores.configuracion import config_twitter
from twython import TwythonAuthError
from LogSodin import LogSodin

class Test_Twitter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.log = LogSodin(cfg, cfg.FICHERO_LOG_MONITOR, LogSodin.LOGGER_MONITOR)
        cls.log.configurar_log()
        cls.twitter = Twitter(cfg, cls.log)
        cls.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        cls.repo_eventos = RepoEventos(cfg, cls.cliente_mongo)
        cls.repo_estaciones = RepoEstaciones(cfg, cls.cliente_mongo)
        cls.repo_nucleos = RepoNucleos(cfg, cls.cliente_mongo)
        cls.repo_tipos_evento = RepoTiposEvento(cfg, cls.cliente_mongo)
        cls.repo_confederaciones = RepoConfederaciones(cfg, cls.cliente_mongo)
        cls.gestion = Gestion(cfg, cls.log)
        cls.coordinador_evento = CoordinadorEvento(cfg, cls.log)        

    def test_autentica_cuenta(self):
        twython_obj = Twitter.autenticar_cuenta(config_twitter.APP_KEY, config_twitter.APP_SECRET)
        self.assertIsNotNone(twython_obj.access_token)

    def test_fuerza_error_autenticacion_control_excepcion(self):
        app_key_fake = 'dHWe2sdfyco9wgfda0cr'
        app_secret_key_fake = 't8sBz4asdffffDRjZLf7BUUxmGYCVqrtZeimzHFoEium'
        with self.assertRaises(TwythonAuthError):
            Twitter.autenticar_cuenta(app_key_fake, app_secret_key_fake)

    def test_filtro_avanzado_tweets(self): 
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()        
        eventos = self.repo_eventos.obtener_eventos()
        evento_fluvial = util.filtrar_lista(eventos, 'codigoTipo', tipo_fluvial['codigo'])
        tweets_filtrados = self.twitter.filtro_avanzado_tweets_evento(evento_fluvial['datosTwitter'], evento_fluvial)
        
        self.assertLess(len(tweets_filtrados), len(evento_fluvial['datosTwitter']))

    def test_obtiene_un_lote_tweets(self):
        tweets_por_lote = 10
        propiedades = self.__props_test(tweets_por_lote)
        resultados = self.twitter.obtener_lote_tweets(propiedades)
        self.assertFalse('errors' in resultados)
        self.assertTrue('search_metadata' in resultados)
        self.assertGreater(resultados['statuses'], 0, 'No han encontrado tweets')

    def test_obtiene_varios_lotes_sin_duplicados(self):
        tweets_por_lote = 4 #Por agilizar
        num_lotes = 2
        propiedades = self.__props_test(tweets_por_lote)
        tweets = self.twitter.busqueda_tweets_por_lotes(propiedades, num_lotes)
        #Comprobar que no se insertan tweets duplicados en un evento
        lista_ids = [t['id'] for t in tweets]
        duplicados = [k for k, v in dict(Counter(lista_ids)).items() if v > 1]
        self.assertTrue(len(duplicados) == 0)

    def test_valida_tweet_con_foto(self):
        query = Twitter.crear_query_twitter('Flooding filter:twimg', '', '', '')
        props = {'query': query, 'query_geo': '', 'id_ultimo': 0, 'next_max_id': None, 'max_num_tweets': 25}
        resultados = self.twitter.obtener_lote_tweets(props)
        tweets = resultados['statuses']
        tweets_con_foto_twitter = [t for t in tweets if self.twitter.tiene_foto(t)]
        self.assertIsNotNone(tweets_con_foto_twitter[0])
        url_foto_twitter = self.twitter.obtener_url_foto_de_tweet(tweets_con_foto_twitter[0])
        respuesta = requests.get(url_foto_twitter, verify=False)

        self.assertTrue('twimg' in url_foto_twitter)
        self.assertTrue(respuesta.status_code == requests.codes.ok)
        self.assertTrue(len(respuesta.content) > 0)

    def test_valida_tweet_con_foto_externa(self):
        query = Twitter.crear_query_twitter('Instagram filter:links', '', '', '')
        props = {'query': query, 'query_geo': '', 'id_ultimo': 0, 'next_max_id': None, 'max_num_tweets': 25}
        resultados = self.twitter.obtener_lote_tweets(props)
        tweets = resultados['statuses']
        tweets_con_foto_externa = [t for t in tweets if self.twitter.tiene_foto_externa(t)]
        self.assertIsNotNone(tweets_con_foto_externa[0])
        url_foto_externa = self.twitter.obtener_url_foto_de_tweet(tweets_con_foto_externa[0])
        respuesta = requests.get(url_foto_externa, verify=False)

        self.assertTrue('instagram' in url_foto_externa)
        self.assertTrue(respuesta.status_code == requests.codes.ok)
        self.assertTrue(len(respuesta.content) > 0)

    def test_filtrar_nombres_propios(self):
        textos = [u'Inundación en el río Gállego',u'Desbordamiento rio Astillero', u'Andando cerca de un astillero', u'Un gallego sale a la calle']
        toponimos = [u'Gállego','Pas','Ebro','Astillero']
        textos_filtrados =[]
       
        for texto in textos:
            if any(re.search(r'\s' + toponimo, texto) for toponimo in toponimos):
                textos_filtrados.append(texto)
        self.assertTrue(len(textos_filtrados) == 2)

    def test_fuerza_error_parseo_url_foto_externa(self):
        url_test = 'https://www.instagram.com/explore/tags/inundaciones/'
        with self.assertRaises(HTMLParser.HTMLParseError):
            self.twitter.sacar_link_a_foto_instagram(url_test)

    def test_fuerza_error_conexion_url_foto_externa(self):
        url_test = 'https://www.sodin_fake_instagram.com'
        tweet_fake = {'entities':{'urls':[{'expanded_url': url_test}]}}
        with self.assertRaises(ConnectionError):
            self.twitter.obtener_url_foto_de_tweet(tweet_fake)

    def test_inserta_tweet_en_evento(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        propiedades = self.__props_test(1)

        resultados = self.twitter.obtener_lote_tweets(propiedades)
        tweets = resultados['statuses']        
        evento_test = None
        
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_fluvial['codigo'])
        toponimos = self.coordinador_evento.crear_lista_toponimos(estacion_test)
        evento_test = self.coordinador_evento.crear_evento(estacion_test['id'], tipo_fluvial['codigo'], toponimos)
        res_evento = self.repo_eventos.insertar_evento(evento_test)
        self.assertIsNotNone(res_evento, 'No se ha insertado el evento en el que guardar la medida')
        res_tweets = self.repo_eventos.insertar_tweets_en_evento(res_evento.inserted_id, tweets)

        self.assertTrue(res_tweets.acknowledged)
        self.assertEqual(res_tweets.modified_count, 1, "No se ha actualizado ningun documento")

        self.repo_eventos.borrar_evento(res_evento.inserted_id)

    def test_probar_geocoding_lote_tweets(self):
        props = self.__props_test(5)
        resultados = self.twitter.obtener_lote_tweets(props)
        tweets_geocodificados = self.twitter.geocodificar_tweets(resultados['statuses'])

        for tweet in tweets_geocodificados:
            self.assertIsNotNone(tweet['coordinates'])
            self.assertIsNotNone(tweet['tipo_geo'])

    def test_prueba_query_real_de_estacion(self): 
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        estacion = self.repo_estaciones.obtener_estacion('A606')
        #estacion = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_fluvial)
        toponimos = self.coordinador_evento.crear_lista_toponimos(estacion)

        query_toponimos = u'"{0}"'.format(toponimos[0])        
        
        for toponimo in toponimos[1:]:            
            query_toponimos += u' OR "{0}"'.format(toponimo)
       
        query = Twitter.crear_query_twitter(query_toponimos, config_twitter.PALABRAS_CLAVE_FLUVIAL,
                                            config_twitter.PALABRAS_EXCLUIDAS, config_twitter.CUENTAS_OFICIALES)
        props = {
            'query': query, 'query_geo': '', 'id_ultimo': 0, 'next_max_id': None,
            'max_num_tweets': 5
            }
        resultados = self.twitter.obtener_lote_tweets(props)
        self.assertIsNotNone(resultados, u'No se ha podido hacer la busqueda. Posible error con la API de Twitter')
        self.assertFalse('errors' in resultados)
        self.assertTrue('search_metadata' in resultados)
        self.assertGreater(resultados['statuses'], 0, 'No han encontrado tweets')

    def test_obtiene_espacialmente_nucleo_cercano(self):
        coords_test = {'lon': -3.9506, 'lat': 43.4268}
        distancia_max = 500
        nucleo = None
        
        while nucleo is None :
            nucleos_cercanos = self.repo_nucleos.obtener_nucleos_cercanos(coords_test, distancia_max)            
            temp_iter = iter(nucleos_cercanos)
            try:
                nucleo = next(temp_iter)
                self.assertTrue(nucleo)                             
            except StopIteration:
                distancia_max += 1000
                continue       
 
    def test_obtiene_espacialmente_nucleo_costero_cercano(self):
        coords_boya_gijon = {'lon': -5.660, 'lat': 43.615}
        distancia_max = 50000 #50km
        nucleo = None
        
        while nucleo is None :
            nucleos_cercanos = self.repo_nucleos.obtener_nucleos_costeros_cercanos(coords_boya_gijon, distancia_max)            
            temp_iter = iter(nucleos_cercanos)
            try:
                nucleo = next(temp_iter)
                self.assertIsNotNone(nucleo)
            except StopIteration:
                distancia_max += 1000
                continue      

    def __obtener_estacion_aleatoria_de_un_tipo(self, tipo):
        confederaciones = self.repo_confederaciones.obtener_confederaciones()
        estaciones_confederacion = []
        while not estaciones_confederacion:
            confederacion_aleatoria = random.choice(confederaciones)
            estaciones_confederacion = self.repo_estaciones.obtener_estaciones_de_tipo(confederacion_aleatoria['codigo'], tipo, True)

        estacion_test = random.choice(estaciones_confederacion)
        return estacion_test

    def __props_test(self, num_tweets_lote):
        # Prueba de busqueda de tweets abierta para asegurar que existan
        # resultados
        query = Twitter.crear_query_twitter('Inundacion OR Riada filter:twimg', '', '', '')
        query_geo = '' #Sin filtro espacial para asegurar resultados
        props = {
            'query': query, 'query_geo': query_geo, 'id_ultimo': 0, 'next_max_id': None,
            'max_num_tweets': num_tweets_lote
            }
        return props

if __name__ == '__main__':
    unittest.main()
