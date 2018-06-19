import unittest
import config_tests as cfg
from proveedores.configuracion import config_instagram
from proveedores.Instagram import Instagram
from LogSodin import LogSodin

class Test_Instagram(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.log = LogSodin(cfg, cfg.FICHERO_LOG_MONITOR, LogSodin.LOGGER_MONITOR)
        cls.log.configurar_log()
        cls.instagram = Instagram(cls.log)

    def test_autentica_instagram(self):
        instagram_api = Instagram.autenticar_instagram(config_instagram.ACCESS_TOKEN,
                                                       config_instagram.CLIENT_SECRET)
        self.assertIsNotNone(instagram_api)

    def test_buscar_posts_por_tag(self):
        posts = self.instagram.buscar_posts("sol")
        self.assertGreater(posts, 0, 'No se han encontrado posts de instagram para ese tag')

if __name__ == '__main__':
    unittest.main()
