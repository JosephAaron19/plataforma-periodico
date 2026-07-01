from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from apps.configuration.views import LandingConfigView

class LandingConfigViewTest(SimpleTestCase):
    """
    Unit tests for LandingConfigView using SimpleTestCase and mocking database requests.
    """
    @patch('apps.configuration.views.ParametroSistema.objects.using')
    def test_get_landing_config(self, mock_using):
        mock_title = MagicMock()
        mock_title.valor_texto = "La información que conecta nuestra región"
        mock_subtitle = MagicMock()
        mock_subtitle.valor_texto = "Noticias locales..."
        mock_bg = MagicMock()
        mock_bg.valor_texto = "http://test.com/bg.png"
        mock_pos = MagicMock()
        mock_pos.valor_texto = "center"

        # Mock sequence for four get_or_create calls
        mock_using.return_value.get_or_create.side_effect = [
            (mock_title, True),
            (mock_subtitle, True),
            (mock_bg, True),
            (mock_pos, True),
        ]

        factory = APIRequestFactory()
        request = factory.get('/api/v1/configuration/landing/')

        view = LandingConfigView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['hero_title'], "La información que conecta nuestra región")
        self.assertEqual(response.data['hero_subtitle'], "Noticias locales...")
        self.assertEqual(response.data['hero_background_url'], "http://test.com/bg.png")
        self.assertEqual(response.data['hero_background_position'], "center")
