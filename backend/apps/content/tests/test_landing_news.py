from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from apps.content.views import NoticiaLandingListCreateView, NoticiaLandingDetailView

class NoticiaLandingViewsTest(SimpleTestCase):
    """
    Unit tests for NoticiaLanding list and detail views.
    """
    @patch('apps.content.views.noticia_landing_views.NoticiaLanding.objects.using')
    def test_get_landing_news(self, mock_using):
        mock_news = MagicMock()
        mock_news.id = 1
        mock_news.titulo = "Noticia de prueba"
        mock_news.descripcion = "Descripcion de prueba"
        mock_news.imagen = "/media/landing_news/abc.jpg"

        # Mock sequence for objects querying
        mock_using.return_value.all.return_value.exists.return_value = True
        mock_using.return_value.all.return_value.order_by.return_value = [mock_news]

        factory = APIRequestFactory()
        request = factory.get('/api/v1/public/news-landing/')

        view = NoticiaLandingListCreateView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['titulo'], "Noticia de prueba")
