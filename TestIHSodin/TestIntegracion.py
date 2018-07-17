# -*- coding: utf-8 -*-
import unittest
import random
import config_tests_integracion as cfg
from Deteccion import Deteccion
from Gestion import Gestion
from datos.RepoUtil import RepoUtil as repo
from datos.RepoVariables import RepoVariables
from datos.RepoEventos import RepoEventos
from datos.RepoEstaciones import RepoEstaciones
from datos.RepoConfederaciones import RepoConfederaciones
from datos.RepoTiposEvento import RepoTiposEvento
from proveedores.Twitter import Twitter
from proveedores.CHCantabrico import CHCantabrico
from CoordinadorEvento import CoordinadorEvento
from Analisis import Analisis
from utiles.Utilidades import Utilidades as util
from LogSodin import LogSodin
from bson import ObjectId

#@unittest.skip("pruebas de integración completas de eventos fluviales y costeros")
class Test_Integracion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.log = LogSodin(cfg, cfg.FICHERO_LOG_MONITOR, LogSodin.LOGGER_MONITOR)
        cls.log.configurar_log()
        cls.chc = CHCantabrico(cfg)
        cls.gestion = Gestion(cfg, cls.log)
        cls.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        cls.repo_confederaciones = RepoConfederaciones(cfg, cls.cliente_mongo)
        cls.repo_estaciones = RepoEstaciones(cfg, cls.cliente_mongo)
        cls.repo_variables = RepoVariables(cfg, cls.cliente_mongo)
        cls.repo_eventos = RepoEventos(cfg, cls.cliente_mongo)
        cls.repo_tipos_evento = RepoTiposEvento(cfg, cls.cliente_mongo)
        cls.analisis = Analisis(cfg, cls.log)
        cls.coordinador = CoordinadorEvento(cfg, cls.log)
        cls.twitter = Twitter(cfg, cls.log)

    #@unittest.skip("prueba completa de eventos fluviales contra BD real")
    def test_ciclo_evento_fluvial_completo(self):
        # Se activa un evento de inundación fluvial (fake) en cada
        # confederacion
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        estaciones_con_evento = self._activar_eventos_fluviales_fake()
        for estacion in estaciones_con_evento:
            self.assertTrue(estacion['activa'])

        # Agregar datos de sensores y rrss a los eventos fluviales
        eventos_activos = self._agregar_datos_evento_fluvial(tipo_fluvial)
        for evento in eventos_activos:
            self.assertTrue(len(evento['datosTwitter']) > 0)
            self.assertTrue(len(evento['datosConfederaciones']) > 0)

        # Desactivar evento y hacer analisis post evento
        eventos_desactivados = self._desactivar_y_analizar_eventos_fake()
        for evento in eventos_desactivados:
            self.assertFalse(evento['activo'])
            post_evento = self.repo_eventos.obtener_post_evento(str(evento['_id']))
            self.assertIsNotNone(post_evento)

            self.repo_eventos.borrar_evento(str(evento['_id']))
            self.repo_eventos.borrar_post_evento(str(post_evento['_id']))

    #unittest.skip("prueba completa de eventos costeros contra BD real")
    def test_ciclo_evento_costero_completo(self):
        # Se activa un evento de inundación costero (fake) en cada
        # confederacion
        tipo_costero = self.repo_tipos_evento.obtener_tipo_evento_costero()
        estaciones_con_evento = self._activar_eventos_costeros_fake()
        for estacion in estaciones_con_evento:
            self.assertTrue(estacion['activa'])

        # Agregar datos de sensores y rrss a los eventos costeros
        eventos_activos = self._agregar_datos_evento_costero(tipo_costero)
        for evento in eventos_activos:
            self.assertTrue(len(evento['datosTwitter']) > 0)
            self.assertTrue(len(evento['datosPuertos']) > 0)

        # Desactivar evento y hacer analisis post evento
        eventos_desactivados = self._desactivar_y_analizar_eventos_fake()
        for evento in eventos_desactivados:
            self.assertFalse(evento['activo'])
            post_evento = self.repo_eventos.obtener_post_evento(str(evento['_id']))
            self.assertIsNotNone(post_evento)

            self.repo_eventos.borrar_evento(str(evento['_id']))
            self.repo_eventos.borrar_post_evento(str(post_evento['_id']))
                
    def test_post_procesar_evento(self):
        eventos = self.repo_eventos.obtener_eventos()
        res = self.analisis.post_proceso_de_evento(eventos[1])
        self.assertTrue(res.acknowledged, "No se ha guardado el postevento procesado")
        self.assertIsInstance(res.inserted_id, ObjectId)

        self.repo_eventos.borrar_post_evento(res.inserted_id)    
        
    def _activar_eventos_fluviales_fake(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial() 
        estaciones_con_evento = []

        for confederacion in self.repo_confederaciones.obtener_confederaciones():
            proveedor_confe = self.repo_confederaciones.obtener_proveedor_saih(confederacion)
            deteccion = Deteccion(cfg, self.log, proveedor_confe)
            estaciones = self.repo_estaciones.obtener_estaciones_de_tipo(confederacion['codigo'], tipo_fluvial['codigo'], True)
            if not estaciones:
                continue
            estacion_seleccionada = random.choice(estaciones)

            variable_deteccion = self.repo_variables.obtener_variable_por_nombre(proveedor_confe.cfg_proveedor.VARIABLE_DETECCION)
            variable_estacion = util.filtrar_lista(estacion_seleccionada['variables'], 'codigo', variable_deteccion['codigo'])
            variable_estacion['umbrales'][proveedor_confe.cfg_proveedor.NIVEL_ALERTA] = 0.01 #Alterar umbral

            deteccion.comprobar_estado_estaciones([estacion_seleccionada], variable_deteccion)
            estaciones_con_evento.append(estacion_seleccionada)

        return estaciones_con_evento

    def _activar_eventos_costeros_fake(self):
        tipo_costero = self.repo_tipos_evento.obtener_tipo_evento_costero() 
        proveedor_boyas = self.repo_confederaciones.obtener_proveedor_boyas()
        estaciones_con_evento = []      
        
        for confederacion in self.repo_confederaciones.obtener_confederaciones():            
            deteccion = Deteccion(cfg, self.log, proveedor_boyas)
            estaciones = self.repo_estaciones.obtener_estaciones_de_tipo(confederacion['codigo'], tipo_costero['codigo'], True)
            if not estaciones:
                continue
            estacion_seleccionada = random.choice(estaciones)

            variable_deteccion = self.repo_variables.obtener_variable_por_nombre(proveedor_boyas.cfg_proveedor.VARIABLE_DETECCION)
            variable_estacion = util.filtrar_lista(estacion_seleccionada['variables'], 'codigo', variable_deteccion['codigo'])
            variable_estacion['umbrales'][proveedor_boyas.cfg_proveedor.NIVEL_ALERTA] = 0.01 #Alterar umbral

            deteccion.comprobar_estado_estaciones([estacion_seleccionada], variable_deteccion)
            estaciones_con_evento.append(estacion_seleccionada)

        return estaciones_con_evento

    def _agregar_datos_evento_fluvial(self, tipo_fluvial):
        eventos_activos = self.repo_eventos.obtener_eventos_activos_de_tipo(tipo_fluvial['codigo'])
        for evento_activo in eventos_activos:
            # In Situ
            estacion = self.repo_estaciones.obtener_estacion(evento_activo['idEstacion'])            
            self.gestion.guardar_datos_de_saih(evento_activo, estacion)

            # RRSS
            tweets = self._query_twitter(estacion, "Rio")
            tweets_con_geo = self.twitter.geocodificar_tweets(tweets)
            self.assertTrue(tweets_con_geo, "No se han encontrado tweets para el evento fake")
            evento_activo['datosTwitter'].extend(tweets_con_geo)
            self.repo_eventos.actualizar_evento(evento_activo)

        return eventos_activos

    def _agregar_datos_evento_costero(self, tipo_costero):
        eventos_activos = self.repo_eventos.obtener_eventos_activos_de_tipo(tipo_costero['codigo'])
        for evento_activo in eventos_activos:
            # In Situ
            estacion = self.repo_estaciones.obtener_estacion(evento_activo['idEstacion'])            
            self.gestion.guardar_datos_de_boyas(evento_activo, estacion)

            # RRSS
            tweets = self._query_twitter(estacion, "Costa")
            tweets_con_geo = self.twitter.geocodificar_tweets(tweets)
            self.assertTrue(tweets_con_geo, "No se han encontrado tweets para el evento fake")
            evento_activo['datosTwitter'].extend(tweets_con_geo)
            self.repo_eventos.actualizar_evento(evento_activo)

        return eventos_activos

    def _query_twitter(self, estacion, descripcion_tipo):
        toponimos = u'"{0}" OR "{1}" OR "{2}"'.format(estacion['rio_costa'], estacion['sistema'], estacion['nombre'])
        query_fake = u"{0} Inundacion OR Inundaciones OR Emergencia OR {1}".format(descripcion_tipo, toponimos)
        props = {
            'query': query_fake, 'query_geo': '', 'id_ultimo': 0, 'next_max_id': None,
            'max_num_tweets': 5
            }
        resultados = self.twitter.obtener_lote_tweets(props)
        return resultados['statuses']

    def _desactivar_y_analizar_eventos_fake(self):
        eventos_activos = self.repo_eventos.obtener_eventos_activos()
        for evento in eventos_activos:
            self.coordinador.desactivar_evento(evento)
            self.coordinador.iniciar_postproceso_evento(evento)

        return eventos_activos

    def __obtener_estacion_aleatoria_de_un_tipo(self, tipo):
        confederaciones = self.repo_confederaciones.obtener_confederaciones()
        estaciones_confederacion = []
        while not estaciones_confederacion:
            confederacion_aleatoria = random.choice(confederaciones)
            estaciones_confederacion = self.repo_estaciones.obtener_estaciones_de_tipo(confederacion_aleatoria['codigo'], tipo['codigo'], True)

        estacion_test = random.choice(estaciones_confederacion)
        return estacion_test

if __name__ == '__main__':
    unittest.main()
