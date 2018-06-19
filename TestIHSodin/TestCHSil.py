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
from proveedores.CHSil import CHSil
from LogSodin import LogSodin
from utiles.Utilidades import Utilidades as util

class Test_CHSil(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.Chsil = CHSil()
        cls.log = LogSodin(cfg, cfg.FICHERO_LOG_MONITOR, LogSodin.LOGGER_MONITOR)
        cls.log.configurar_log()
        cls.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        cls.repo_variables = RepoVariables(cfg, cls.cliente_mongo)
        cls.repo_eventos = RepoEventos(cfg, cls.cliente_mongo)
        cls.repo_estaciones = RepoEstaciones(cfg, cls.cliente_mongo)
        cls.repo_tipos_evento = RepoTiposEvento(cfg, cls.cliente_mongo)            
        cls.CODIGO_CONFEDERACION_SIL = 2

    def test_conexion_chsil(self):
        conexion_ok = self.Chsil.hay_conexion('HTTP', self.Chsil.cfg_proveedor.URL)
        self.assertTrue(conexion_ok)

    def test_pide_html_con_datos(self):        
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()        
        for variable_estacion in estacion_test['variables']:
            codigo_html = self.Chsil.descargar_html_con_datos(variable_estacion['signal'])        
            self.assertIsNotNone(codigo_html, 'La descarga del html de la url ha fallado.')

    def test_lanza_excepcion_en_error_peticion(self):
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(self.Chsil.cfg_proveedor.VARIABLE_DETECCION)        
        variable_estacion = util.filtrar_lista(estacion_test['variables'], 'codigo', variable_deteccion['codigo'])

        self.Chsil.cfg_proveedor.URL = self.Chsil.cfg_proveedor.URL.replace('.php', '.com')
        parametros = self.Chsil.crear_parametros_peticion(variable_estacion['signal'])

        with self.assertRaises(IOError):
            self.Chsil.hacer_peticion_http(parametros)

        self.Chsil.cfg_proveedor.URL = self.Chsil.cfg_proveedor.URL.replace('.com', '.php') #volver a poner bien la url del proveedor

    def test_lee_medidas_de_html(self):
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()

        for variable_estacion in estacion_test['variables']:
            html_variable = self.Chsil.descargar_html_con_datos(variable_estacion['signal'])
            medida = self.Chsil.extraer_medida_de_html(estacion_test['id'], variable_estacion['codigo'], html_variable)
            self.assertIsNotNone(medida)

    def test_inserta_ultima_medida_de_estacion(self):
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(self.Chsil.cfg_proveedor.VARIABLE_DETECCION)
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()
        medida = self.Chsil.ultima_medida_de_estacion(estacion_test, variable_deteccion)
        self.assertIsNotNone(medida)
        self.assertIsNotNone(medida.idEstacion)
        self.assertIsNotNone(medida.codigoVariable)
        self.assertTrue(medida.fecha)
        self.assertTrue(medida.valor)

        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        
        evento_test = None
        
        #Crear evento fake
        coordinador = CoordinadorEvento(cfg, self.log)
        toponimos = coordinador.crear_lista_toponimos(estacion_test)
        evento_test = coordinador.crear_evento(estacion_test['id'], tipo_fluvial['codigo'], toponimos)
        res_evento = self.repo_eventos.insertar_evento(evento_test)
        self.assertIsNotNone(res_evento, 'No se ha insertado el evento en el que guardar la medida')
        res = self.repo_eventos.insertar_medida_en_evento(res_evento.inserted_id, medida)

        self.assertTrue(res.acknowledged)
        self.assertEqual(res.modified_count, 1, "No se ha actualizado ningun documento")

        self.repo_eventos.borrar_evento(res_evento.inserted_id)

    def __obtener_estacion_aleatoria_del_proveedor(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        estaciones_confederacion = self.repo_estaciones.obtener_estaciones_de_tipo(self.CODIGO_CONFEDERACION_SIL, tipo_fluvial['codigo'], True)
        return random.choice(estaciones_confederacion)      

    @unittest.skip("prueba integral de todas las estaciones del proveedor")
    def test_chequeo_integral_estaciones_chsil(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        estaciones = self.repo_estaciones.obtener_estaciones_de_tipo(self.CODIGO_CONFEDERACION_SIL, tipo_fluvial['codigo'], True)
        
        for estacion in estaciones:
            try:
                for variable_estacion in estacion['variables']:
                    variable = self.repo_variables.obtener_variable(variable_estacion['codigo'])
                    html = self.Chsil.descargar_html_con_datos(variable_estacion['signal'])
                    medida = self.Chsil.extraer_medida_de_html(estacion['id'], variable['codigo'], html)                                   
                    self.assertIsNotNone(medida)               
                    self.log.escribir(u'Datos de {0} en {1} obtenidos correctamente'.format(variable['nombre'], estacion['nombre']), self.log.INFO)

            except Exception as ex:
                self.log.escribir(u'Error obteniendo datos de {0} en {1}. Detalle: {2}'.format(variable['nombre'], estacion['nombre'], ex.message), self.log.WARNING)
                continue
                #self.fail('Error obteniendo datos de {0}'.format(estacion['nombre']))

if __name__ == '__main__':
    unittest.main()
