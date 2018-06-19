# -*- coding: utf-8 -*-

import unittest
import random
import config_tests as cfg
from Deteccion import Deteccion
from datos.RepoUtil import RepoUtil as repo
from datos.RepoVariables import RepoVariables
from datos.RepoEventos import RepoEventos
from datos.RepoEstaciones import RepoEstaciones
from datos.RepoConfederaciones import RepoConfederaciones
from datos.RepoTiposEvento import RepoTiposEvento
from utiles.Utilidades import Utilidades as util
from LogSodin import LogSodin

class Test_Deteccion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.log = LogSodin(cfg, cfg.FICHERO_LOG_MONITOR, LogSodin.LOGGER_MONITOR)
        cls.log.configurar_log()        
        cls.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        cls.repo_confederaciones = RepoConfederaciones(cfg, cls.cliente_mongo)
        cls.repo_estaciones = RepoEstaciones(cfg, cls.cliente_mongo)
        cls.repo_variables = RepoVariables(cfg, cls.cliente_mongo)
        cls.repo_eventos = RepoEventos(cfg, cls.cliente_mongo)
        cls.repo_tipos_evento = RepoTiposEvento(cfg, cls.cliente_mongo)        

    def test_detecta_evento_fluvial(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()     
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_fluvial)        
        proveedor_confe = self.repo_confederaciones.obtener_proveedor_saih(self.repo_confederaciones.obtener_confederacion(estacion_test['codigoConfederacion']))
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(proveedor_confe.cfg_proveedor.VARIABLE_DETECCION)
        deteccion = Deteccion(cfg, self.log, proveedor_confe)

        valor_umbral = 0
        hay_alerta = deteccion.evaluar_datos_actuales(estacion_test, variable_deteccion, valor_umbral)
        self.assertTrue(hay_alerta)
        valor_umbral = 9999
        hay_alerta = deteccion.evaluar_datos_actuales(estacion_test, variable_deteccion, valor_umbral)
        self.assertFalse(hay_alerta)        

    def test_estacion_sin_umbral_devuelve_nulo(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()     
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_fluvial)

        proveedor_confe = self.repo_confederaciones.obtener_proveedor_saih(self.repo_confederaciones.obtener_confederacion(estacion_test['codigoConfederacion']))
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(proveedor_confe.cfg_proveedor.VARIABLE_DETECCION)
        deteccion = Deteccion(cfg, self.log, proveedor_confe)

        # Quitar umbral para simular una estacion sin esa información
        umbral = estacion_test['variables'][0]['umbrales'][proveedor_confe.cfg_proveedor.NIVEL_ALERTA]
        if umbral is not None:
            estacion_test['variables'][0]['umbrales'][proveedor_confe.cfg_proveedor.NIVEL_ALERTA] = None
            umbral_post = deteccion.obtener_umbral(estacion_test, variable_deteccion['codigo'],proveedor_confe.cfg_proveedor.NIVEL_ALERTA)
            self.assertIsNone(umbral_post)               

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
