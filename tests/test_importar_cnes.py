import unittest
from unittest.mock import patch
from scripts.importar_cnes import normalize, contains, number, find_source, SOURCE

class ImportTests(unittest.TestCase):
    def setUp(self):
        self.cities = {'521380': {'id':'5213806','name':'Morrinhos','uf':'GO'}, '530010': {'id':'5300108','name':'Brasília','uf':'DF'}}
        self.geo = {'5213806': {'type':'Polygon','coordinates': [[[-50,-19],[-48,-19],[-48,-17],[-50,-17],[-50,-19]]]}}
        self.row = dict(CNES='0023914',UF='52',IBGE='521380',NOME=' UBS  Teste ',LOGRADOURO=' Rua  A ',BAIRRO='Centro',LATITUDE='-17.8',LONGITUDE='-49,1')
    def test_real_schema_numeric_uf_and_six_digit_city(self):
        item = normalize(self.row,self.cities,self.geo)
        self.assertEqual((item['cnes'],item['city'],item['uf'],item['lon']),('0023914','Morrinhos','GO',-49.1))
        self.assertEqual(item['address'],'Rua A')
    def test_missing_coordinates_preserves_unit(self):
        self.row['LATITUDE']=''
        item=normalize(self.row,self.cities,self.geo)
        self.assertIsNone(item['lat']);self.assertIsNone(item['lon']);self.assertEqual(item['coordinate_status'],'ausente')
    def test_outside_city_never_becomes_marker(self):
        self.row['LATITUDE']='-16'
        item=normalize(self.row,self.cities,self.geo)
        self.assertIsNone(item['lat']);self.assertEqual(item['coordinate_status'],'fora_do_municipio')
    def test_non_finite_numbers(self):
        for v in ['NaN','Infinity','',None]: self.assertIsNone(number(v))
    def test_invalid_city_stops_import(self):
        self.row['IBGE']='999999'
        with self.assertRaises(ValueError):normalize(self.row,self.cities,self.geo)
    def test_uf_mismatch_stops_import(self):
        self.row['UF']='35'
        with self.assertRaises(ValueError):normalize(self.row,self.cities,self.geo)
    def test_invalid_identifier_stops_import(self):
        self.row['CNES']='garbage'
        with self.assertRaises(ValueError):normalize(self.row,self.cities,self.geo)
    def test_df_legacy_code_is_preserved(self):
        self.row.update(IBGE='530040',UF='53')
        item=normalize(self.row,self.cities,self.geo)
        self.assertEqual(item['city'],'Brasília');self.assertEqual(item['source_city_code'],'530040')
    def test_polygon_hole(self):
        g={'type':'Polygon','coordinates':[[[0,0],[10,0],[10,10],[0,10],[0,0]],[[4,4],[6,4],[6,6],[4,6],[4,4]]]}
        self.assertTrue(contains(g,1,1));self.assertFalse(contains(g,5,5));self.assertFalse(contains(g,11,1))
    def test_catalog_failure_uses_verified_official_resource(self):
        with patch('scripts.importar_cnes.download',return_value=b'<html>changed</html>'):
            self.assertEqual(find_source()[0],SOURCE)

if __name__=='__main__':unittest.main()
