# -*- coding: utf-8 -*-
'''Programa de monitorización de estaciones ante posibles eventos'''

import version
import config as cfg
from datos.RepoConfederaciones import RepoConfederaciones
from datos.RepoTiposEvento import RepoTiposEvento
from datos.RepoUtil import RepoUtil as repo
from Deteccion import Deteccion
from LogSodin import LogSodin

def main():
    log = inicializar_log()

    try:
        cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        repo_confederaciones = RepoConfederaciones(cfg, cliente_mongo)
        repo_tipos_evento = RepoTiposEvento(cfg, cliente_mongo)
        ejecucion_ok = True

        log.escribir(u'-- DETECCIÓN DE EVENTOS INICIADO (v{0}) --'.format(version.__version__), log.INFO)
        confederaciones = repo_confederaciones.obtener_confederaciones()

        for confederacion in confederaciones:
            log.escribir(u'---- {0} ---'.format(confederacion['nombre']).upper(), log.INFO)
            ## Detección alertas fluviales #
            proveedor_saih = repo_confederaciones.obtener_proveedor_saih(confederacion)
            tipo_fluvial = repo_tipos_evento.obtener_tipo_evento_fluvial()
            deteccion_fluvial = Deteccion(cfg, log, proveedor_saih)
            if not proveedor_saih:
                log.escribir(u' No hay proveedor de datos fluviales para esta confederación', log.WARNING)
            else:
                log.escribir(u'-- Alertas fluviales --', log.INFO)
                deteccion_fluvial.buscar_alertas(confederacion, tipo_fluvial)

            ## Detección alertas costeras #
            proveedor_boyas = repo_confederaciones.obtener_proveedor_boyas()
            tipo_costero = repo_tipos_evento.obtener_tipo_evento_costero()
            deteccion_costera = Deteccion(cfg, log, proveedor_boyas)

            log.escribir(u'-- Alertas costeras --', log.INFO)
            deteccion_costera.buscar_alertas(confederacion, tipo_costero)

            log.escribir('--------------------------------------------------', log.INFO)

    except Exception as ex:
        ejecucion_ok = False
        log.escribir(u'Se ha producido un error, {0}'.format(ex), log.ERROR)
    finally:
        repo.insertar_ejecucion(cliente_mongo, ejecucion_ok, 'Deteccion')
        log.escribir(u'Datos de ejecucion del operacional guardados', log.INFO)
        log.escribir(u'-- FIN DETECCIÓN DE EVENTOS --', log.INFO)

def inicializar_log():
    log = LogSodin(cfg, cfg.FICHERO_LOG_MONITOR, LogSodin.LOGGER_MONITOR)
    log.configurar_log()
    return log

if __name__ == '__main__':
    main()
