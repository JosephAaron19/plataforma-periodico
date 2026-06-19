from django.test import SimpleTestCase
from apps.companies.models.empresa import Empresa
from apps.companies.models.empresa_identidad import EmpresaIdentidad
from apps.companies.models.empresa_configuracion import EmpresaConfiguracion
from apps.companies.models.empresa_historial import EmpresaHistorial

class CompanyModelsSanityTest(SimpleTestCase):
    """
    Sanity tests to verify that company models are unmanaged, mapped to the correct
    PostgreSQL schema/tables, and define correct fields.
    """
    def test_empresa_model_metadata(self):
        self.assertFalse(Empresa._meta.managed)
        self.assertEqual(Empresa._meta.db_table, 'pdg"."emp_empresa')

    def test_empresa_identidad_model_metadata(self):
        self.assertFalse(EmpresaIdentidad._meta.managed)
        self.assertEqual(EmpresaIdentidad._meta.db_table, 'pdg"."evi_empresa_identidad')

    def test_empresa_configuracion_model_metadata(self):
        self.assertFalse(EmpresaConfiguracion._meta.managed)
        self.assertEqual(EmpresaConfiguracion._meta.db_table, 'pdg"."ecf_empresa_configuracion')

    def test_empresa_historial_model_metadata(self):
        self.assertFalse(EmpresaHistorial._meta.managed)
        self.assertEqual(EmpresaHistorial._meta.db_table, 'pdg"."ehi_empresa_historial')
