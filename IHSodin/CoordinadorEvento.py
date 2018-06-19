# -*- coding: utf-8 -*-
import pytz
import warnings
from datetime import *
from dateutil import parser
from dateutil.relativedelta import *
from datos.RepoUtil import RepoUtil as repo
from datos.RepoEventos import RepoEventos
from datos.RepoTiposEvento import RepoTiposEvento
from datos.RepoNucleos import RepoNucleos
from Gestion import Gestion
from modelos.Evento import Evento
from Analisis import Analisis
from utiles.Utilidades import Utilidades as util

warnings.filterwarnings("ignore", category=UnicodeWarning)

class CoordinadorEvento(object):
    """Clase que coordina el ciclo de vida de un evento de inundacion"""

    def __init__(self, cfg, log):
        self.cfg = cfg
        self.log = log
        self.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        self.analisis = Analisis(self.cfg, self.log)
        self.gestion = Gestion(self.cfg, self.log)
        self.repo_eventos = RepoEventos(cfg, self.cliente_mongo)
        self.repo_nucleos = RepoNucleos(cfg, self.cliente_mongo)
        self.repo_tipos_evento = RepoTiposEvento(cfg, self.cliente_mongo)        

    def gestionar_alerta(self, estacion, variable, hay_alerta):
        '''Comprueba el estado de las alertas en una estacion,
        gestionando un nuevo evento o actualizando uno existente'''
        evento_estacion = self.obtener_evento_en_estacion(estacion, variable['codigoTipoEvento'])
        if not hay_alerta and evento_estacion:
            #Si no hay alerta y existe un evento, hay que desactivarlo            
            if not self.evento_mas_24h(evento_estacion['fechaInicio']):
                #Si no han pasado 24h el evento se mantiene activo
                self.log.escribir(u' - Valores normalizados en las primeras 24h, el EVENTO SIGUE ACTIVO', self.log.INFO)
                return
            
            self.desactivar_evento(evento_estacion)
            self.iniciar_postproceso_evento(evento_estacion)
            return

        if hay_alerta and evento_estacion is None:
            #Si hay alerta y no existe un evento en BD hay que crear uno
            toponimos = self.crear_lista_toponimos(estacion)
            res_evento = self.guardar_evento_nuevo(estacion['id'], variable['codigoTipoEvento'], toponimos)
            self.log.escribir(u' - Valores superan umbral, NUEVO EVENTO ACTIVADO', self.log.INFO)
            #Insertar datos iniciales en el nuevo evento
            nuevo_evento = self.repo_eventos.obtener_evento(res_evento)
            self.gestion.actualizar_datos_eventos([nuevo_evento])            
            return res_evento

        if hay_alerta and evento_estacion:
            self.log.escribir(u' - Valores superan umbral, el EVENTO SIGUE ACTIVO', self.log.INFO)
            return
        
    def evento_mas_24h(self, fecha_inicio_evento):                  
        utc = pytz.timezone(u'UTC')
        fecha_utc = utc.localize(fecha_inicio_evento)
        ahora = datetime.now(pytz.utc)
        ayer = ahora + relativedelta(days=-1)

        return fecha_utc < ayer

    def obtener_evento_en_estacion(self, estacion, cod_tipo):
        '''Devuelve el evento activo en la estacion o None si no hay ninguno'''
        eventos_activos = self.repo_eventos.obtener_eventos_activos_de_tipo(cod_tipo)
        return util.filtrar_lista(eventos_activos, 'idEstacion', estacion['id'])

    def desactivar_evento(self, evento):
        evento['activo'] = False
        evento['fechaFin'] = util.fecha_actual(self.cfg.FORMATO_FECHA)
        res = self.repo_eventos.actualizar_evento(evento)
        if res.modified_count == 1:
            self.log.escribir(u' - Valores normalizados, EVENTO DESACTIVADO', self.log.INFO)
        else:
            self.log.escribir(u' - No se ha podido desactivar el evento. Error actualizando la BD', self.log.WARNING)

    def iniciar_postproceso_evento(self, evento):
        self.log.escribir(u' Iniciando Análisis y PostProceso del Evento', self.log.INFO)
        res = self.analisis.post_proceso_de_evento(evento)
        if res.acknowledged:
            self.log.escribir(u' PostEvento guardado con éxito', self.log.INFO)
        else:
            self.log.escribir(u' No se ha podido almacenar el PostEvento', self.log.WARNING)

    def guardar_evento_nuevo(self, id_estacion, cod_tipo_evento, toponimos):
        evento = self.crear_evento(id_estacion, cod_tipo_evento, toponimos)
        res = self.repo_eventos.insertar_evento(evento)
        return res.inserted_id

    def crear_evento(self, id_estacion, cod_tipo, toponimos):
        try:
            nuevo_evento = Evento({
                'fechaInicio' : util.fecha_actual_str(self.cfg.FORMATO_FECHA),
                'fechaFin': None,
                'codigoTipo' : cod_tipo,
                'idEstacion' : id_estacion,
                'activo': True,
                'toponimos': toponimos,
                'datosAemet': [],
                'datosPuertos':[],
                'datosConfederaciones':[],
                'datosTwitter':[]
                })
            return nuevo_evento
        except AttributeError as aterr:
            raise AttributeError(u'Error creando nuevo evento. {0}'.format(aterr.message))


    def crear_lista_toponimos(self, estacion):
        # Crear query con un máximo de 200 caracteres.  La busqueda en twitter
        # está limitada #
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        lista_toponimos = []        

        # Topónimos de la estación fluvial / costera
        lista_toponimos.extend([estacion['nombre'], estacion['rio_costa'], estacion['sistema']])
        
        if estacion['codigoTipo'] == tipo_fluvial['codigo']:
            # Topónimos de núcleos cercanos a la estación fluvial
            distancia_max = 4000 #4km
            nombres_nucleos_cercanos = self.repo_nucleos.obtener_nucleos_cercanos(estacion['coordenadas'], distancia_max)            
        else:
            # Topónimos de núcleos costeros cercanos a la boya
            distancia_max = 40000 #40km
            nombres_nucleos_cercanos = self.repo_nucleos.obtener_nucleos_costeros_cercanos(estacion['coordenadas'], distancia_max)

        for nombre in nombres_nucleos_cercanos:
            #Hay que limitar los caracteres de la lista de toponimos a un
            #máximo de 200 por si acaso.
            #La query final no puede superar los 500 (max de la api de twitter)
            if nombre.find(".") != -1: #Controlar que no entren nombres con caracteres que rompan la api de twitter
                continue
                
            lista_toponimos.append(nombre)            
            if len(str(lista_toponimos)) > 175:
                break            
            
        return lista_toponimos