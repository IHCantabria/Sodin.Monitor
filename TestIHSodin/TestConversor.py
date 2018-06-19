# -*- coding: utf-8 -*-

import unittest
import datetime
from modelos.Medida import Medida
from utiles.Conversor import Conversor

class Test_Conversor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conversor = Conversor()
        cls.medida = Medida({
            'codigoConfederacion': 1,
            'idEstacion': 'N020',#Pontenova
            'codigoVariable' : 0,#Nivel agua
            'fecha': '09-02-2017 15:30',
            'valor': 2.14})

    def test_convierte_clase_a_objeto_python(self):
        self.assertNotEqual(type(self.medida), type({}))
        self.medida = self.medida.to_json_obj()
        self.assertTrue(self.medida)
        self.assertEqual(type(self.medida), type({}))

    def test_lanza_error_atributo_en_conversion(self):
        self.medida.fecha = datetime.datetime.now() # Forzar error de atributo
        with self.assertRaises(AttributeError):
            self.medida.to_json_obj()

    def test_convierte_clase_a_json(self):
        self.assertNotEqual(type(self.medida), type(''))
        self.medida = self.medida.to_json_str()
        self.assertTrue(self.medida)
        self.assertEqual(type(self.medida), type(''))


if __name__ == '__main__':
    unittest.main()
