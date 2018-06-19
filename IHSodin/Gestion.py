# -*- coding: utf-8 -*-
from datos.RepoUtil import RepoUtil as repo
from datos.RepoEventos import RepoEventos
from datos.RepoEstaciones import RepoEstaciones
from datos.RepoConfederaciones import RepoConfederaciones
from datos.RepoTiposEvento import RepoTiposEvento
from datos.RepoVariables import RepoVariables
from proveedores.Twitter import Twitter
from proveedores.configuracion import config_twitter

class Gestion(object):
    """Clase para gestionar los eventos mientras permanecen activos"""

    def __init__(self, cfg, log):
        self.cfg = cfg
        self.log = log
        self.cliente_mongo = repo.inicializar_cliente(cfg.URI_MONGODB, cfg.NOMBRE_BD)
        self.repo_confederaciones = RepoConfederaciones(cfg, self.cliente_mongo)
        self.repo_estaciones = RepoEstaciones(cfg, self.cliente_mongo)
        self.repo_eventos = RepoEventos(cfg, self.cliente_mongo)
        self.repo_variables = RepoVariables(cfg, self.cliente_mongo)
        self.repo_tipo_evento = RepoTiposEvento(cfg, self.cliente_mongo)
        self.twitter = Twitter(self.cfg, self.log)

    def actualizar_datos_eventos(self, eventos_activos):
        '''Obtiene los ultimos datos y los guarda en el evento'''
        for evento in eventos_activos:
            self.guardar_datos_en_evento(evento)
            self.repo_eventos.actualizar_evento(evento)
            self.log.escribir(u'OK - Evento actualizado con los últimos datos',
                              self.log.INFO)

    def guardar_datos_en_evento(self, evento):
        estacion = self.repo_estaciones.obtener_estacion(evento['idEstacion'])
        tipo = self.repo_eventos.obtener_tipo_evento(evento['codigoTipo'])
        self.log.escribir(u'EVENTO {0} activo en {1}. Fecha: {2}'
                          .format(tipo['nombre'], estacion['nombre'], evento['fechaInicio']), self.log.INFO)
        if tipo == self.repo_tipo_evento.obtener_tipo_evento_fluvial():
            # datos de estaciones saih para eventos fluviales
            self.log.escribir(u'1) Obtener últimos datos de estaciones SAIH para el evento', self.log.INFO)
            self.guardar_datos_de_saih(evento, estacion)
        else:
            # datos de boyas de puertos del estado para eventos costeros
            self.log.escribir(u'1) Obtener últimos datos de boyas para el evento', self.log.INFO)
            self.guardar_datos_de_boyas(evento, estacion)

        # datos twitter
        self.log.escribir(u'2) Buscar nuevos tweets sobre el evento', self.log.INFO)
        self.guardar_nuevos_tweets_evento(evento, estacion)

        # datos aemet?

    def guardar_datos_de_saih(self, evento, estacion):
        confederacion = self.repo_confederaciones.obtener_confederacion(estacion['codigoConfederacion'])
        proveedor_confe = self.repo_confederaciones.obtener_proveedor_saih(confederacion)

        for variable_estacion in estacion['variables']:
            variable = self.repo_variables.obtener_variable(variable_estacion['codigo'])
            try:
                ultima_medida = proveedor_confe.ultima_medida_de_estacion(estacion, variable)
                Gestion._agregar_medida_a_evento(evento, 'datosConfederaciones', ultima_medida)
                self.log.escribir(u'Último dato de {0} añadido al evento'.format(variable['nombre']),
                                  self.log.INFO)
            except ValueError as verr:
                self.log.escribir(u'No se ha podido obtener la medida. {0}'.format(verr.message), self.log.WARNING)
                continue

    def guardar_datos_de_boyas(self, evento, estacion):
        proveedor_boyas = self.repo_confederaciones.obtener_proveedor_boyas()
        for variable_estacion in estacion['variables']:
            variable = self.repo_variables.obtener_variable(variable_estacion['codigo'])
            try:
                ultima_medida = proveedor_boyas.ultima_medida_de_estacion(estacion, variable)
                Gestion._agregar_medida_a_evento(evento, 'datosPuertos', ultima_medida)
                self.log.escribir(u'Último dato de {0} añadido al evento'.format(variable['nombre']),
                                  self.log.INFO)
            except ValueError as verr:
                self.log.escribir(u'No se ha podido obtener la medida. {0}'.format(verr.message), self.log.WARNING)
                continue

    def guardar_nuevos_tweets_evento(self, evento, estacion):
        '''Busca y guarda nuevos tweets relacionados con un evento concreto'''

        # Configurar peticion de busqueda en twitter
        props = self.propiedades_peticion_twitter(evento, estacion)

        # Buscar nuevos tweets por lotes
        tweets = self.twitter.busqueda_tweets_por_lotes(props, config_twitter.NUM_LOTES)        
        self.log.escribir(u'Filtro avanzado de tweets', self.log.INFO)
        tweets_filtrados = self.twitter.filtro_avanzado_tweets_evento(tweets, evento)

        # Guardar nuevos tweets en evento de BD
        if not tweets_filtrados:
            self.log.escribir(u'No se han encontrado nuevos tweets sobre el evento', self.log.INFO)

        evento['datosTwitter'].extend(tweets_filtrados)         
        self.log.escribir(u'{0} nuevos tweets agregados al evento'.format(str(len(tweets_filtrados))), self.log.INFO)

    @staticmethod
    def _agregar_medida_a_evento(evento, campo_datos, medida):
        '''Agrega una medida de una estación a un evento'''
        evento[campo_datos].append(medida.to_json_obj())        

    def propiedades_peticion_twitter(self, evento, estacion):
        tipo_fluvial = self.repo_tipo_evento.obtener_tipo_evento_fluvial()
        toponimos = evento['toponimos']
        query_toponimos = u'"{0}"'.format(toponimos[0])        
        
        for toponimo in toponimos[1:]:            
            query_toponimos += u' OR "{0}"'.format(toponimo)        
        
        if evento['codigoTipo'] == tipo_fluvial['codigo']:
            query = self.twitter.crear_query_twitter(query_toponimos, config_twitter.PALABRAS_CLAVE_FLUVIAL, config_twitter.PALABRAS_EXCLUIDAS,
                                                 config_twitter.CUENTAS_OFICIALES)
        else:
            query = self.twitter.crear_query_twitter(query_toponimos, config_twitter.PALABRAS_CLAVE_COSTERO, config_twitter.PALABRAS_EXCLUIDAS,
                                                 config_twitter.CUENTAS_OFICIALES)

        #Activar para filtrar espacialmente la búsqueda de tweets
        #coords = Gestion.obtener_centroide_estacion(estacion)
        #query_geo = Twitter.crear_query_geo(coords[0], coords[1])
        query_geo = ''

        id_ultimo_tweet = self.obtener_id_ultimo_tweet_evento(evento)

        return {
            'query': query,
            'query_geo': query_geo,
            'id_ultimo': id_ultimo_tweet,
            'next_max_id': None,
            'max_num_tweets': config_twitter.MAX_TWEETS_PETICION
            }    

    def obtener_id_ultimo_tweet_evento(self, evento):
        '''Obtiene la id del último tweet de un evento guardado en la BD'''
        id_ultimo_tweet = 0

        try:
            id_ultimo_tweet = evento['datosTwitter'][0]['id']
        except IndexError:
            self.log.escribir(u'Aun no hay tweets en el evento', self.log.DEBUG)
        finally:
            return id_ultimo_tweet    

    @staticmethod
    def obtener_centroide_estacion(estacion_evento):
        try:
            return (estacion_evento['coordenadas']['lon'],
                    estacion_evento['coordenadas']['lat'])
        except AttributeError as atterr:
            raise AttributeError(u'Error obteniendo centroide de un evento. {0}'
                                 .format(atterr.message))
