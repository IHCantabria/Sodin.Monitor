# -*- coding: utf-8 -*-

from datos.RepoVariables import RepoVariables
from datos.RepoEstaciones import RepoEstaciones
from datos.RepoUtil import RepoUtil as repo
from CoordinadorEvento import CoordinadorEvento
from utiles.Utilidades import Utilidades as util

class Deteccion(object):
    """Clase para la gestión de las alertas fluviales y costeras"""

    def __init__(self, cfg, log, proveedor_datos):
        self.cfg = cfg
        self.log = log
        self.proveedor_datos = proveedor_datos
        self.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        self.coordinador = CoordinadorEvento(cfg, self.log)
        self.repo_variables = RepoVariables(self.cfg, self.cliente_mongo)
        self.repo_estaciones = RepoEstaciones(self.cfg, self.cliente_mongo)

    def buscar_alertas(self, confederacion, tipo):
        '''Comprobar posibles alertas de inundación fluvial o costera en una zona'''
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(self.proveedor_datos.cfg_proveedor.VARIABLE_DETECCION)
        estaciones = self.repo_estaciones.obtener_estaciones_de_tipo(confederacion['codigo'], tipo['codigo'], True)
        if not estaciones:
            self.log.escribir(u' No hay estaciones de tipo {0} en esta confederación'.format(tipo['nombre']), self.log.INFO)
        else:
            self.log.escribir(u' Comprobar {0} en estaciones: '.format(variable_deteccion['nombre'].upper()),
                              self.log.INFO)
            self.comprobar_estado_estaciones(estaciones, variable_deteccion)

    def comprobar_estado_estaciones(self, estaciones, variable_deteccion):
        for estacion in estaciones:
            try:                
                umbral = Deteccion.obtener_umbral(estacion, variable_deteccion['codigo'],
                                                  self.proveedor_datos.cfg_proveedor.NIVEL_ALERTA)
                hay_alerta = self.evaluar_datos_actuales(estacion, variable_deteccion, umbral)
                self.coordinador.gestionar_alerta(estacion, variable_deteccion, hay_alerta)
            except Exception as ex:
                self.log.escribir(u' {0}: {1}'.format(estacion['nombre'], ex.message), self.log.WARNING)
                continue

    @staticmethod
    def obtener_umbral(estacion, cod_variable, nivel_alerta):
        variable_estacion = util.filtrar_lista(estacion['variables'], 'codigo', cod_variable)
        if not variable_estacion:
            raise ValueError(u' Variable de detección no disponible')

        if variable_estacion['umbrales'][nivel_alerta]:
            return variable_estacion['umbrales'][nivel_alerta]
        return None

    def evaluar_datos_actuales(self, estacion, variable_deteccion, umbral):
        '''Comprueba si los valores actuales de una variable superan los umbrales de la estación'''
        if umbral is None:
            raise ValueError(u' Umbral no definido.')

        medida = self.proveedor_datos.ultima_medida_de_estacion(estacion, variable_deteccion)
        self.log.escribir(u' {0}: {1}. Umbral: {2}'.format(estacion['nombre'], str(medida.valor),
                                                           str(umbral)), self.log.INFO)
        hay_alerta = Deteccion.valores_superan_umbral(umbral, medida.valor)
        return hay_alerta

    @staticmethod
    def valores_superan_umbral(umbral, valor):
        if umbral is not None and valor > umbral:
            return True
        return False
