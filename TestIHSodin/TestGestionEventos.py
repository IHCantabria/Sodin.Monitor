# -*- coding: utf-8 -*-
import unittest
import random
import pytz
from datetime import datetime, timedelta
from dateutil import parser
from dateutil.relativedelta import *
import config_tests as cfg
from datos.RepoUtil import RepoUtil as repo
from datos.RepoVariables import RepoVariables
from datos.RepoEventos import RepoEventos
from datos.RepoEstaciones import RepoEstaciones
from datos.RepoConfederaciones import RepoConfederaciones
from datos.RepoTiposEvento import RepoTiposEvento
from CoordinadorEvento import CoordinadorEvento
from Gestion import Gestion
from LogSodin import LogSodin
from utiles.Utilidades import Utilidades as util
from modelos.Evento import Evento
from bson.objectid import ObjectId

class Test_GestionEventos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.log = LogSodin(cfg, cfg.FICHERO_LOG_GESTOR, LogSodin.LOGGER_MONITOR)
        cls.log.configurar_log()
        cls.gestion = Gestion(cfg, cls.log)
        cls.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        cls.repo_confederaciones = RepoConfederaciones(cfg, cls.cliente_mongo)
        cls.repo_variables = RepoVariables(cfg, cls.cliente_mongo)
        cls.repo_estaciones = RepoEstaciones(cfg, cls.cliente_mongo)
        cls.repo_eventos = RepoEventos(cfg, cls.cliente_mongo)
        cls.repo_tipos_evento = RepoTiposEvento(cfg, cls.cliente_mongo)
        cls.cod_tipo_evento_fluvial = 1
        cls.Coordinador = CoordinadorEvento(cfg, cls.log)
        cls.id_estacion = 'N020' #Pontenova
        cls.cod_chc = 1
        cls.nivel_rio = 2.14


    def test_agrega_ultimos_datos_de_estacion_a_evento_fluvial(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()       
                        
        # Crear evento fake        
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_fluvial)
        toponimos = self.Coordinador.crear_lista_toponimos(estacion_test)
        nuevo_evento_obj = self.Coordinador.crear_evento(estacion_test['id'], tipo_fluvial['codigo'], toponimos)
        res_evento = self.repo_eventos.insertar_evento(nuevo_evento_obj)
        self.assertIsNotNone(res_evento, 'No se ha insertado el evento en el que agregar los ultimos datos')
        
        evento = self.repo_eventos.obtener_evento(res_evento.inserted_id)
        medidas_conf = len(evento['datosConfederaciones'])
        num_variables = len(estacion_test['variables'])
        medidas_totales = medidas_conf + num_variables

        self.gestion.guardar_datos_de_saih(evento, estacion_test)
        self.assertGreaterEqual(len(evento['datosConfederaciones']), medidas_totales,
                                "No se han agregado todos los datos que debería medir la estación")

        #Comprobar que la medida es de por lo menos las últimas 3 horas desde
        #el presente
        hora_ultima_medida = evento['datosConfederaciones'][-1]['fecha']
        ultima_hora = datetime.utcnow() - timedelta(hours=3)
        self.assertTrue(hora_ultima_medida > ultima_hora)

        self.repo_eventos.borrar_evento(res_evento.inserted_id)

    def test_agrega_ultimos_datos_de_estacion_a_evento_costero(self):
        tipo_costero = self.repo_tipos_evento.obtener_tipo_evento_costero()                        
        
        #Si no hay ningún evento activo, crear uno fake          
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_costero)
        toponimos = self.Coordinador.crear_lista_toponimos(estacion_test)
        nuevo_evento_obj = self.Coordinador.crear_evento(estacion_test['id'], tipo_costero['codigo'], toponimos)
        res_evento = self.repo_eventos.insertar_evento(nuevo_evento_obj)
        self.assertIsNotNone(res_evento, 'No se ha insertado el evento en el que agregar los ultimos datos')
        
        evento = self.repo_eventos.obtener_evento(res_evento.inserted_id)
        medidas_boya = len(evento['datosPuertos'])
        num_variables = len(estacion_test['variables'])
        medidas_totales = medidas_boya + num_variables

        self.gestion.guardar_datos_de_boyas(evento, estacion_test)
        self.assertGreaterEqual(len(evento['datosPuertos']), medidas_totales,
                                "No se han agregado todos los datos que debería medir la estación")

        #Comprobar que la medida es de por lo menos las últimas 3 horas desde
        #el presente
        hora_ultima_medida = evento['datosPuertos'][-1]['fecha']
        ultima_hora = datetime.utcnow() - timedelta(hours=3)
        self.assertTrue(hora_ultima_medida > ultima_hora)

        self.repo_eventos.borrar_evento(res_evento.inserted_id)

    def test_activa_y_desactiva_gestion_de_evento_fluvial(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()     
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_fluvial)        
        proveedor_confe = self.repo_confederaciones.obtener_proveedor_saih(self.repo_confederaciones.obtener_confederacion(estacion_test['codigoConfederacion']))
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(proveedor_confe.cfg_proveedor.VARIABLE_DETECCION)

        # Activar gestion alerta
        inserted_id = self.Coordinador.gestionar_alerta(estacion_test, variable_deteccion, True)
        eventos_activos = self.repo_eventos.obtener_eventos_activos_de_tipo(tipo_fluvial['codigo'])
        evento_estacion = util.filtrar_lista(eventos_activos, 'idEstacion', estacion_test['id'])
        self.assertIsNotNone(evento_estacion)
        self.assertTrue(evento_estacion['activo'])        

        # Desactiva gestion alerta
        self.Coordinador.desactivar_evento(evento_estacion)
        self.assertFalse(evento_estacion['activo'])
        self.assertIsNotNone(evento_estacion['fechaFin'])

        self.repo_eventos.borrar_evento(inserted_id)

    def test_activa_y_desactiva_gestion_de_evento_costero(self):
        tipo_costero = self.repo_tipos_evento.obtener_tipo_evento_costero()        
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_costero)        
        proveedor_boyas = self.repo_confederaciones.obtener_proveedor_boyas()
        variable_deteccion = self.repo_variables.obtener_variable_por_nombre(proveedor_boyas.cfg_proveedor.VARIABLE_DETECCION)

        # Activar gestion alerta
        inserted_id = self.Coordinador.gestionar_alerta(estacion_test, variable_deteccion, True)
        eventos_activos = self.repo_eventos.obtener_eventos_activos_de_tipo(tipo_costero['codigo'])
        evento_estacion = util.filtrar_lista(eventos_activos, 'idEstacion', estacion_test['id'])
        self.assertIsNotNone(evento_estacion)        
        self.assertTrue(evento_estacion['activo'])        

        # Desactiva gestion alerta
        self.Coordinador.desactivar_evento(evento_estacion)
        self.assertFalse(evento_estacion['activo'])
        self.assertIsNotNone(evento_estacion['fechaFin'])

        self.repo_eventos.borrar_evento(inserted_id)

    def test_inserta_un_evento_nuevo(self):
        evento = self.__crear_evento()
        res = self.repo_eventos.insertar_evento(evento)
        self.assertTrue(res.acknowledged)
        self.assertIsInstance(res.inserted_id, ObjectId)

        self.repo_eventos.borrar_evento(res.inserted_id)

    def test_obtiene_los_eventos_activos(self):
        eventos_activos = self.repo_eventos.obtener_eventos_activos()
        for evento in eventos_activos:
            self.assertTrue(evento['activo'])

    def test_comprueba_evento_mas_24h(self):
        tipo_fluvial = self.repo_tipos_evento.obtener_tipo_evento_fluvial()
        estacion_test = self.__obtener_estacion_aleatoria_de_un_tipo(tipo_fluvial)
        toponimos = self.Coordinador.crear_lista_toponimos(estacion_test)

        nuevo_evento = self.Coordinador.crear_evento(estacion_test['id'], tipo_fluvial['codigo'], toponimos)
        fecha_inicio = parser.parse(nuevo_evento.fechaInicio, dayfirst=True) + relativedelta(days=-2)
        self.assertTrue(self.Coordinador.evento_mas_24h(fecha_inicio))

        fechaActual = datetime.now()        
        self.assertFalse(self.Coordinador.evento_mas_24h(fechaActual))

    def __crear_evento(self):
        return Evento({
            'fechaInicio' : util.fecha_actual_str(cfg.FORMATO_FECHA),
            'fechaFin': util.fecha_actual_str(cfg.FORMATO_FECHA),
            'codigoTipo' : self.cod_tipo_evento_fluvial,
            'idEstacion' : self.id_estacion,
            'activo': True,
            'toponimos': [],
            'datosAemet': [],
            'datosPuertos':[],
            'datosConfederaciones':[],
            'datosTwitter':[],
            'datosInstagram':[]
            })

    def __obtener_estacion_aleatoria_de_un_tipo(self, tipo):
        confederaciones = self.repo_confederaciones.obtener_confederaciones()
        estaciones_confederacion = []
        while not estaciones_confederacion:
            confederacion_aleatoria = random.choice(confederaciones)
            estaciones_confederacion = self.repo_estaciones.obtener_estaciones_de_tipo(confederacion_aleatoria['codigo'], tipo['codigo'], True)

        estacion_test = random.choice(estaciones_confederacion)
        return estacion_test


if __name__ == '__main__':
    unittest.main()
