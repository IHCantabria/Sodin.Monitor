import unittest
import os
import config_tests as cfg
from LogSodin import LogSodin

class Test_Log(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.log = LogSodin(cfg, cfg.FICHERO_LOG_MONITOR, LogSodin.LOGGER_MONITOR)
        cls.log.configurar_log()

    def test_crea_y_escribe_fichero_log(self):
        ruta_log = os.path.join(cfg.RUTA_BASE_EJECUCIONES, cfg.CARPETA_LOG, cfg.FICHERO_LOG_MONITOR)
        if os.path.exists(ruta_log):
            try:
                os.remove(ruta_log)
            except Exception:
                pass
        self.log.escribir("Test DEBUG level", self.log.DEBUG)
        self.log.escribir("Test INFO level", self.log.INFO)
        self.log.escribir("Test WARNING level", self.log.WARNING)
        self.log.escribir("Test ERROR level", self.log.ERROR)

        self.assertTrue(os.path.exists(ruta_log), 'No se ha generado el fichero de log')

if __name__ == '__main__':
    unittest.main()
