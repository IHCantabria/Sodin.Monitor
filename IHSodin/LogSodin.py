# -*- coding: utf-8 -*-

import os
import logging
import logging.handlers

class LogSodin(object):
    """Clase para configuración y gestión del log del sistema"""

    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'

    LOGGER_MONITOR = 'MONITOR-SODIN'
    LOGGER_EVENTO = 'GESTOR-SODIN'

    def __init__(self, cfg, nombre_fichero, nombre_logger):
        self.cfg = cfg
        self.logger = logging.getLogger(nombre_logger)
        self.nombre_fichero = nombre_fichero

    def configurar_log(self):
        self.logger.setLevel(logging.INFO)
        # Log en consola
        consola = logging.StreamHandler()
        consola.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s [%(levelname)-5s] [%(name)-10s] %(message)s',
                                      datefmt='%d-%m %H:%M')
        consola.setFormatter(formatter)
        self.logger.addHandler(consola)

        # Log en fichero (concurrente)
        fichero_log = os.path.join(self.cfg.RUTA_BASE_EJECUCIONES, self.cfg.CARPETA_LOG,
                                   self.nombre_fichero)
        hdlr_fichero = logging.handlers.RotatingFileHandler(fichero_log, 'a', 512 * 1024, 10,
                                                            None, 0)
        hdlr_fichero.setLevel(logging.INFO)
        hdlr_fichero.setFormatter(formatter)
        self.logger.addHandler(hdlr_fichero)

    def escribir(self, msg, tipo):
        msg.encode('utf8', 'replace')
        if tipo == logging.getLevelName(10):
            self.logger.debug(msg)
        if tipo == logging.getLevelName(20):
            self.logger.info(msg)
        if tipo == logging.getLevelName(30):
            self.logger.warning(msg)
        if tipo == logging.getLevelName(40):
            self.logger.error(msg)
