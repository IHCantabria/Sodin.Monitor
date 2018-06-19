# -*- coding: utf-8 -*-
import unittest
import random
import config_tests as cfg
from datos.RepoUtil import RepoUtil as repo
from datos.RepoEventos import RepoEventos
from datos.RepoVariables import RepoVariables
from datos.RepoEstaciones import RepoEstaciones
from datos.RepoTiposEvento import RepoTiposEvento
from CoordinadorEvento import CoordinadorEvento
from proveedores.CHEbro import CHEbro
from LogSodin import LogSodin

class Test_CHEbro(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.Chebro = CHEbro()
        cls.log = LogSodin(cfg, cfg.FICHERO_LOG_MONITOR, LogSodin.LOGGER_MONITOR)
        cls.log.configurar_log()
        cls.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        cls.repo_variables = RepoVariables(cfg, cls.cliente_mongo)
        cls.repo_eventos = RepoEventos(cfg, cls.cliente_mongo)
        cls.repo_estaciones = RepoEstaciones(cfg, cls.cliente_mongo)
        cls.repo_tipos_evento = RepoTiposEvento(cfg, cls.cliente_mongo)        
        cls.CODIGO_CONFEDERACION_CHEBRO = 3        

    def test_conexion_chebro(self):
        conexion_ok = self.Chebro.hay_conexion('HTTP', self.Chebro.cfg_proveedor.URL)
        self.assertTrue(conexion_ok)

    def test_pide_json_con_datos(self):
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()
        for variable_estacion in estacion_test['variables']:
            datos_json = self.Chebro.descargar_json_con_datos(variable_estacion['signal'])      
            self.assertIsNotNone(datos_json, 'La obtencion del json de la api ha fallado.')                      
        
    def test_lee_medidas_de_json(self):        
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()

        for variable_estacion in estacion_test['variables']:
            datos_json = self.Chebro.descargar_json_con_datos(variable_estacion['signal'])
            medida = self.Chebro.extraer_medida_de_json(estacion_test['id'], variable_estacion['codigo'], datos_json)
            self.assertIsNotNone(medida)

    def test_inserta_ultima_medida_de_estacion(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()        
        evento_test = None
        id_evento = None
        
        #Crear evento fake para proveedor
        coordinador = CoordinadorEvento(cfg, self.log)
        toponimos = coordinador.crear_lista_toponimos(estacion_test)
        evento_test = coordinador.crear_evento(estacion_test['id'], tipo_fluvial['codigo'], toponimos)
        res_evento = self.repo_eventos.insertar_evento(evento_test)
        self.assertIsNotNone(res_evento, 'No se ha insertado el evento en el que guardar la medida')
        id_evento = res_evento.inserted_id
            
        for variable_estacion in estacion_test['variables']:
            variable = self.repo_variables.obtener_variable(variable_estacion['codigo'])
            medida = self.Chebro.ultima_medida_de_estacion(estacion_test, variable)
            self.assertIsNotNone(medida)
            self.assertIsNotNone(medida.idEstacion)
            self.assertIsNotNone(medida.codigoVariable)
            self.assertTrue(medida.fecha)
            self.assertGreaterEqual(medida.valor, 0)

            res = self.repo_eventos.insertar_medida_en_evento(id_evento, medida)
            self.assertTrue(res.acknowledged)
            self.assertEqual(res.modified_count, 1, "No se ha actualizado ningun documento")
       
        self.repo_eventos.borrar_evento(res_evento.inserted_id)

    def __obtener_estacion_aleatoria_del_proveedor(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        estaciones_confederacion = self.repo_estaciones.obtener_estaciones_de_tipo(self.CODIGO_CONFEDERACION_CHEBRO, tipo_fluvial['codigo'], True)
        return random.choice(estaciones_confederacion)
            
    @unittest.skip("prueba integral de todas las estaciones de la chebro")
    def test_chequeo_integral_estaciones_chebro(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        estaciones = self.repo_estaciones.obtener_estaciones_de_tipo(self.CODIGO_CONFEDERACION_CHEBRO, tipo_fluvial['codigo'], True)        
        for estacion in estaciones:
            try:
                for variable_estacion in estacion['variables']:
                    variable = self.repo_variables.obtener_variable(variable_estacion['codigo'])                    
                    datos_json = self.Chebro.descargar_json_con_datos(variable_estacion['signal'])
                    medida = self.Chebro.extraer_medida_de_json(estacion['id'], variable['codigo'], datos_json)                                                      
                    self.assertIsNotNone(medida)               
                    self.log.escribir(u'Datos de {0} en {1} obtenidos correctamente'.format(variable['nombre'], estacion['nombre']), self.log.INFO)

            except Exception as ex:
                self.log.escribir(u'Error obteniendo datos de {0} en {1}. Detalle: {2}'.format(variable['nombre'], estacion['nombre'], ex.message), self.log.WARNING)
                continue
                #self.fail('Error obteniendo datos de
                #{0}'.format(estacion['nombre']))
if __name__ == '__main__':
    unittest.main()
