# -*- coding: utf-8 -*-

import unittest
import random
import os
import httplib
import requests
import config_tests as cfg
from proveedores.CHCantabrico import CHCantabrico
from CoordinadorEvento import CoordinadorEvento
from datos.RepoTiposEvento import RepoTiposEvento
from datos.RepoEstaciones import RepoEstaciones
from datos.RepoUtil import RepoUtil as repo
from datos.RepoVariables import RepoVariables
from datos.RepoEventos import RepoEventos
from LogSodin import LogSodin

@unittest.skip("Proveedor desactivado")
class Test_CHCantabrico(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.Chc = CHCantabrico(cfg)
        cls.log = LogSodin(cfg, cfg.FICHERO_LOG_MONITOR, LogSodin.LOGGER_MONITOR)
        cls.log.configurar_log()
        cls.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        cls.repo_variables = RepoVariables(cfg, cls.cliente_mongo)
        cls.repo_eventos = RepoEventos(cfg, cls.cliente_mongo)
        cls.repo_estaciones = RepoEstaciones(cfg, cls.cliente_mongo)
        cls.repo_tipos_evento = RepoTiposEvento(cfg, cls.cliente_mongo)              
        cls.CODIGO_CONFEDERACION_CHC = 1

    def test_descarga_y_borrado_csv(self):
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(self.Chc.cfg_proveedor.VARIABLE_DETECCION)
        fichero_descargado = self.Chc.descargar_csv_con_variable(estacion_test['id'], variable_deteccion['codigo'])

        self.assertIsNotNone(fichero_descargado, 'El fichero no se ha descargado')
        self.assertTrue(os.path.exists(fichero_descargado), 'El fichero no existe')
        self.Chc.borrar_fichero(fichero_descargado)
        self.assertFalse(os.path.exists(fichero_descargado), "El fichero no se ha podido borrar")

    def test_conexion_chcantabrico(self):
        try:
            conexion_ok = self.Chc.hay_conexion('HTTP', self.Chc.cfg_proveedor.URL)
        except IOError:
            self.fail("Error conectando con proveedor CHC")

    def test_verifica_rutas_descarga(self):
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(self.Chc.cfg_proveedor.VARIABLE_DETECCION)
        (parametros, ruta_completa) = self.Chc.preparar_descarga(estacion_test['id'], variable_deteccion['codigo'])
        ruta_carpeta = ruta_completa[:ruta_completa.rfind('\\')]
        conexion = requests.get(self.Chc.cfg_proveedor.URL, parametros, verify=False)
        self.assertTrue(conexion.status_code == httplib.OK)
        self.assertTrue(os.path.exists(ruta_carpeta))

    def test_lee_datos_de_csv(self):
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()
        for variable_estacion in estacion_test['variables']:
            fichero_descargado = self.Chc.descargar_csv_con_variable(estacion_test['id'], variable_estacion['codigo'])
            medida = self.Chc.extraer_medida_de_csv(estacion_test['id'], variable_estacion['codigo'], fichero_descargado)
            self.assertIsNotNone(medida)        

    def test_lanza_excepcion_en_error_descarga(self):
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(self.Chc.cfg_proveedor.VARIABLE_DETECCION)
        (parametros, ruta_completa) = self.Chc.preparar_descarga(estacion_test['id'], variable_deteccion['codigo'])

        url_rota = self.Chc.cfg_proveedor.URL.replace('.es', '.com')
        with self.assertRaises(IOError):
            requests.get(url_rota, parametros, verify=False)

    def test_lanza_excepcion_en_error_borrado(self):
        ruta_falsa = r'C:\Temp\fichero_falso.csv'

        with self.assertRaises(OSError):
            self.Chc.borrar_fichero(ruta_falsa)

    def test_valida_objeto_medida(self):
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()
        fecha = '09-02-2017 15:30'
        nivel_rio = 2.14
        var_deteccion = self.repo_variables.obtener_variable_por_nombre(self.Chc.cfg_proveedor.VARIABLE_DETECCION)
        fila_csv_test = [fecha, nivel_rio]
        medida = self.Chc.crear_medida_saih(estacion_test['id'], var_deteccion['codigo'],
                                            fila_csv_test[0], fila_csv_test[1])

        self.assertIsNotNone(medida.idEstacion)
        self.assertIsNotNone(medida.codigoVariable)
        self.assertTrue(medida.fecha)
        self.assertTrue(medida.valor)

    def test_inserta_ultima_medida_de_estacion(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        estacion_test = self.__obtener_estacion_aleatoria_del_proveedor()
        lista_test_eventos = self.repo_eventos.obtener_eventos_activos_de_tipo(tipo_fluvial['codigo'])
        evento_test = None
        id_evento = None

        if lista_test_eventos:
            evento_test = lista_test_eventos[-1] #Coger el más reciente / último
            id_evento = evento_test['_id']            
        else:
            #Si no hay ningún evento activo, crear uno fake
            coordinador = CoordinadorEvento(cfg, self.log)
            evento_test = coordinador.crear_evento(estacion_test['id'], tipo_fluvial['codigo'])
            res_evento = self.repo_eventos.insertar_evento(evento_test)
            self.assertIsNotNone(res_evento, 'No se ha insertado el evento en el que guardar la medida')
            id_evento = res_evento.inserted_id
            
        for variable_estacion in estacion_test['variables']:
            variable = self.repo_variables.obtener_variable(variable_estacion['codigo'])
            medida = self.Chc.ultima_medida_de_estacion(estacion_test, variable_estacion)            
            self.assertIsNotNone(medida)
            self.assertIsNotNone(medida.idEstacion)
            self.assertIsNotNone(medida.codigoVariable)
            self.assertTrue(medida.fecha)
            self.assertGreaterEqual(medida.valor, 0)

            res = self.repo_eventos.insertar_medida_en_evento(id_evento, medida)
            self.assertTrue(res.acknowledged)
            self.assertEqual(res.modified_count, 1, "No se ha actualizado ningun documento")       

    def __obtener_estacion_aleatoria_del_proveedor(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        estaciones_confederacion = self.repo_estaciones.obtener_estaciones_de_tipo(self.CODIGO_CONFEDERACION_CHC, tipo_fluvial['codigo'], True)
        return random.choice(estaciones_confederacion)

    #@unittest.skip("prueba integral de las estaciones del proveedor")
    def test_chequeo_integral_estaciones_chc(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        estaciones = self.repo_estaciones.obtener_estaciones_de_tipo(self.CODIGO_CONFEDERACION_CHC, tipo_fluvial['codigo'], True)
        
        for estacion in estaciones:
            try:
                for variable_estacion in estacion['variables']:
                    variable = self.repo_variables.obtener_variable(variable_estacion['codigo'])
                    fichero_descargado = self.Chc.descargar_csv_con_variable(estacion['id'], variable_estacion['codigo'])  
                    medida = self.Chc.extraer_medida_de_csv(estacion['id'], variable_estacion['codigo'], fichero_descargado)                    
                    self.assertIsNotNone(medida)
                    self.Chc.borrar_fichero(fichero_descargado)
            except Exception as ex:
                self.log.escribir(u'Error obteniendo datos de {0} en {1}. Detalle: {2}'.format(variable['nombre'], estacion['nombre'], ex.message), self.log.WARNING)
                continue
                #self.fail('Error obteniendo datos de {0}'.format(estacion['nombre']))


if __name__ == '__main__':
    unittest.main()
