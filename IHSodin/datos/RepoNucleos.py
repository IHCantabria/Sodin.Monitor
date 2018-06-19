# -*- coding: utf-8 -*-
from bson.son import SON

class RepoNucleos(object):
    '''Clase para gestionar la consulta e insercion de datos de Estaciones'''

    def __init__(self, configuracion, cliente_mongo):
        self.cfg = configuracion
        self.bd_mongo = cliente_mongo

    def obtener_nucleos_cercanos(self, coords, distancia_metros):
        punto_geojson = {"coordinates": [coords['lon'], coords['lat']]}        
        query = {"geometry": SON([("$nearSphere", punto_geojson), ("$maxDistance", distancia_metros)])}
        nucleos_cercanos = self.bd_mongo.nucleos.find(query)

        return nucleos_cercanos.distinct('properties.NOMBRE')

    def obtener_nucleos_costeros_cercanos(self, coords, distancia_metros):
        punto_geojson = {"coordinates": [coords['lon'], coords['lat']]}        
        query = {"geometry": SON([("$nearSphere", punto_geojson), ("$maxDistance", distancia_metros)])}
        nucleos_costeros_cercanos = self.bd_mongo.nucleosCosteros.find(query)

        return nucleos_costeros_cercanos.distinct('properties.NOMBRE')
