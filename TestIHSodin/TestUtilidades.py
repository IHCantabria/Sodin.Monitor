import unittest
import datetime
import config_tests as cfg
from utiles.Utilidades import Utilidades as util
from datos.RepoUtil import RepoUtil as repo
from datos.RepoConfederaciones import RepoConfederaciones
from pymongo.errors import OperationFailure

class Test_Utilidades(unittest.TestCase):

    def test_autenticacion(self):
        bad_credentials = 'mongodb://ihLocalUser:badpassword@localhost:27017/TestSodinDeteccionBD?authMechanism=SCRAM-SHA-1'
        cliente_fake = repo.inicializar_cliente(bad_credentials, cfg.NOMBRE_BD)
        cliente_bien = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)

        with self.assertRaises(OperationFailure):
            repo_confederaciones = RepoConfederaciones(cfg, cliente_fake)
            confederacion = repo_confederaciones.obtener_confederacion(1)

        repo_confederaciones = RepoConfederaciones(cfg, cliente_bien)
        confederacion = repo_confederaciones.obtener_confederacion(1)
        self.assertIsNotNone(confederacion)

    def test_comprueba_parseo_cadena_a_fecha(self):
        cadena_fecha = "09-02-2017 15:30"
        cadena_error = "test-error"
        formato = "%d-%m-%Y %H:%M"

        try:
            # Parseo correcto
            fecha = util.convertir_cadena_a_fecha(cadena_fecha, formato)
            self.assertIsNotNone(fecha)
            self.assertIsInstance(fecha, datetime.datetime)
            # Forzar el error de parseo
            util.convertir_cadena_a_fecha(cadena_error, formato)
        except Exception as ex:
            self.assertTrue(isinstance(ex, ValueError))


if __name__ == '__main__':
    unittest.main()
