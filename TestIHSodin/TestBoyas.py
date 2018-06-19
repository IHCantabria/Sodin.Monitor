# -*- coding: utf-8 -*-
import unittest
import random
import config_tests as cfg
from datos.RepoUtil import RepoUtil as repo
from datos.RepoEventos import RepoEventos
from datos.RepoVariables import RepoVariables
from datos.RepoEstaciones import RepoEstaciones
from datos.RepoConfederaciones import RepoConfederaciones
from datos.RepoTiposEvento import RepoTiposEvento
from CoordinadorEvento import CoordinadorEvento
from proveedores.BoyasPuertos import BoyasPuertos
from utiles.Utilidades import Utilidades as util
from LogSodin import LogSodin

class Test_Boyas(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.Boyas = BoyasPuertos()
        cls.log = LogSodin(cfg, cfg.FICHERO_LOG_MONITOR, LogSodin.LOGGER_MONITOR)
        cls.log.configurar_log()
        cls.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        cls.repo_confe = RepoConfederaciones(cfg, cls.cliente_mongo)
        cls.repo_estaciones = RepoEstaciones(cfg, cls.cliente_mongo)
        cls.repo_eventos = RepoEventos(cfg, cls.cliente_mongo)
        cls.repo_variables = RepoVariables(cfg, cls.cliente_mongo)
        cls.repo_tipos_evento = RepoTiposEvento(cfg, cls.cliente_mongo)
        cls.repo_confederaciones = RepoConfederaciones(cfg, cls.cliente_mongo)

    def test_conexion_boyas(self):
        tipo_costero = self.repo_tipos_evento.obtener_tipo_evento_costero()        
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_costero)

        try:
            peticion_http = '{0}/{1}/1'.format(self.Boyas.cfg_proveedor.URL, estacion_test['variables'][0]['signal'])
            conexion_ok = self.Boyas.hay_conexion('HTTP', peticion_http)
            self.assertTrue(conexion_ok, 'No se ha podido conectar al proveedor')
        except IOError as ioerr:
            self.fail('No se ha podido conectar al proveedor.{0}'.format(ioerr.message))

    def test_pide_json_con_datos(self):
        tipo_costero = self.repo_tipos_evento.obtener_tipo_evento_costero()        
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_costero)
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(self.Boyas.cfg_proveedor.VARIABLE_DETECCION)
        
        variable_estacion = util.filtrar_lista(estacion_test['variables'], 'codigo', variable_deteccion['codigo'])

        datos_json = self.Boyas.descargar_json_con_datos(variable_estacion['signal'], 1)
        self.assertIsNotNone(datos_json, 'La descarga del html de la url ha fallado.')   
        
    def test_lee_medidas_de_json(self):
        tipo_costero = self.repo_tipos_evento.obtener_tipo_evento_costero()        
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_costero)

        for variable_estacion in estacion_test['variables']:
            json_variable = self.Boyas.descargar_json_con_datos(variable_estacion['signal'], 1)            
            medida = self.Boyas.extraer_medida_de_json(estacion_test['id'], variable_estacion['codigo'], json_variable)
            self.assertIsNotNone(medida)        

    def test_inserta_ultima_medida_de_boya(self):
        tipo_costero = self.repo_tipos_evento.obtener_tipo_evento_costero()        
        evento_test = None
        estacion_test = None
        id_evento = None
               
        #Crear evento costero fake
        coordinador = CoordinadorEvento(cfg, self.log)
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_costero)
        toponimos = coordinador.crear_lista_toponimos(estacion_test)
        evento_test = coordinador.crear_evento(estacion_test['id'], tipo_costero['codigo'], toponimos)
        res_evento = self.repo_eventos.insertar_evento(evento_test)
        self.assertIsNotNone(res_evento, 'No se ha insertado el evento en el que guardar la medida')
        id_evento = res_evento.inserted_id

        for variable_estacion in estacion_test['variables']:
            variable = self.repo_variables.obtener_variable(variable_estacion['codigo'])
            medida = self.Boyas.ultima_medida_de_estacion(estacion_test, variable)
            self.assertIsNotNone(medida)
            self.assertIsNotNone(medida.idEstacion)
            self.assertIsNotNone(medida.codigoVariable)
            self.assertTrue(medida.fecha)
            self.assertTrue(medida.valor)

            res = self.repo_eventos.insertar_medida_boya_en_evento(id_evento, medida)
            self.assertTrue(res.acknowledged)
            self.assertEqual(res.modified_count, 1, "No se ha actualizado ningun documento")

        self.repo_eventos.borrar_evento(res_evento.inserted_id)

    def __obtener_estacion_aleatoria_de_un_tipo(self, tipo):
        confederaciones = self.repo_confederaciones.obtener_confederaciones()
        estaciones_confederacion = []
        while not estaciones_confederacion:
            confederacion_aleatoria = random.choice(confederaciones)
            estaciones_confederacion = self.repo_estaciones.obtener_estaciones_de_tipo(confederacion_aleatoria['codigo'], tipo['codigo'], True)

        estacion_test = random.choice(estaciones_confederacion)
        return estacion_test

    @unittest.skip("prueba integral de las estaciones del proveedor")
    def test_chequeo_integral_estaciones_boyas(self):
        tipo_costero = self.repo_tipos_evento.obtener_tipo_evento_costero()
        estaciones = self.repo_estaciones.obtener_estaciones_activas_de_tipo(tipo_costero['codigo'])
        
        for estacion in estaciones:
            try:
                for variable_estacion in estacion['variables']:
                    json_variable = self.Boyas.descargar_json_con_datos(variable_estacion['signal'], 1)            
                    medida = self.Boyas.extraer_medida_de_json(estacion['id'], variable_estacion['codigo'], json_variable)
                    self.assertIsNotNone(medida)       
            except Exception as ex:
                self.fail('Error obteniendo datos de {0}. {1}'.format(estacion['nombre'], ex.message))

if __name__ == '__main__':
    unittest.main()
