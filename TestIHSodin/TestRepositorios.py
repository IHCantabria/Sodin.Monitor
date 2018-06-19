# -*- coding: utf-8 -*-

import unittest
import config_tests as cfg
from datos.RepoUtil import RepoUtil as repo
from datos.RepoVariables import RepoVariables
from datos.RepoEventos import RepoEventos
from datos.RepoEstaciones import RepoEstaciones
from datos.RepoConfederaciones import RepoConfederaciones
from bson.objectid import ObjectId
from proveedores.CHCantabrico import CHCantabrico

class Test_Repositorios(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chc = CHCantabrico(cfg)
        cls.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        cls.repo_confederaciones = RepoConfederaciones(cfg, cls.cliente_mongo)
        cls.repo_estaciones = RepoEstaciones(cfg, cls.cliente_mongo)
        cls.repo_variables = RepoVariables(cfg, cls.cliente_mongo)
        cls.repo_eventos = RepoEventos(cfg, cls.cliente_mongo)
        cls.nombre_tipo_fluvial = 'Fluvial'
        cls.cod_tipo_fluvial = 1
        cls.cod_chc = 1 #CHCantabrico

    def test_obtiene_confederacion(self):
        confederacion = self.repo_confederaciones.obtener_confederacion(self.cod_chc)
        self.assertIsNotNone(confederacion)

    def test_obtiene_estaciones_activas(self):
        estaciones = self.repo_estaciones.obtener_estaciones(self.cod_chc, True)

        self.assertGreater(estaciones, 0, "La consulta no ha devuelto resultados")
        for estacion in estaciones:
            self.assertTrue(estacion['activa'], "La consulta no ha filtrado correctamente los activos")

    def test_obtiene_estaciones_de_tipo(self):
        estaciones = self.repo_estaciones.obtener_estaciones_de_tipo(self.cod_chc, self.cod_tipo_fluvial, True)

        self.assertGreater(estaciones, 0, "La consulta no ha devuelto estaciones")
        for estacion in estaciones:
            self.assertTrue(estacion['activa'], "La consulta no ha filtrado correctamente los activos")
            self.assertTrue(estacion['codigoTipo'] == self.cod_tipo_fluvial, "La consulta no ha filtrado correctamente el tipo de estacion")

    def test_obtiene_un_tipo_de_evento(self):
        tipo_evento = self.repo_eventos.obtener_tipo_evento(self.cod_tipo_fluvial)
        self.assertIsNotNone(tipo_evento)
        self.assertEqual(tipo_evento['nombre'], self.nombre_tipo_fluvial)

    def test_obtiene_variables_de_un_tipo(self):
        variables = self.repo_variables.obtener_variables_de_tipo(self.cod_tipo_fluvial)
        self.assertGreater(variables, 0)

    def test_obtiene_eventos_activos_de_un_tipo(self):
        eventos = self.repo_eventos.obtener_eventos_activos_de_tipo(self.cod_tipo_fluvial)
        for evento in eventos:
            self.assertTrue(evento['activo'])
            self.assertTrue(evento['codigoTipo'] == self.cod_tipo_fluvial)

    def test_obtiene_variable_de_un_tipo(self):
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(self.chc.cfg_proveedor.VARIABLE_DETECCION)
        self.assertTrue(variable_deteccion['nombre'] == 'Nivel')
        self.assertIsNotNone(variable_deteccion['codigo'])
        self.assertIsNotNone(variable_deteccion['unidad'])
        self.assertIsNotNone(variable_deteccion['codigoTipoEvento'])

    def test_inserta_datos_ejecucion(self):
        res = repo.insertar_ejecucion(self.cliente_mongo, True, 'Deteccion')

        self.assertTrue(res.acknowledged)
        self.assertIsInstance(res.inserted_id, ObjectId)


if __name__ == '__main__':
    unittest.main()
