# -*- coding: utf-8 -*-
''' Programa para gestionar los eventos de inundación existentes'''

import config as cfg
import version
from LogSodin import LogSodin
from Gestion import Gestion
from datos.RepoEventos import RepoEventos
from datos.RepoUtil import RepoUtil as repo

def main():
    log = inicializar_log()

    try:
        cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        repo_eventos = RepoEventos(cfg, cliente_mongo)
        gestion = Gestion(cfg, log)
        ejecucion_ok = True

        log.escribir(u'-- GESTIÓN DE EVENTOS INICIADO (v{0}) --'.format(version.__version__),
                     log.INFO)

        # Procesar posibles eventos activos
        log.escribir(u'Buscar eventos activos...', log.INFO)
        eventos_activos = repo_eventos.obtener_eventos_activos()

        if eventos_activos:
            gestion.actualizar_datos_eventos(eventos_activos)
        else:
            log.escribir(u'No hay eventos activos', log.INFO)

    except Exception as ex:
        ejecucion_ok = False
        log.escribir(u'Se ha producido un error, {0}'.format(ex), log.ERROR)
    finally:
        repo.insertar_ejecucion(cliente_mongo, ejecucion_ok, 'Gestion')
        log.escribir(u'-- FIN GESTIÓN DE EVENTOS --', log.INFO)

def inicializar_log():
    log = LogSodin(cfg, cfg.FICHERO_LOG_GESTOR, LogSodin.LOGGER_EVENTO)
    log.configurar_log()
    return log


if __name__ == '__main__':
    main()
