from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from apps.editions.views import EdicionLandingListCreateView, EdicionLandingDetailView

class EdicionLandingViewsTest(SimpleTestCase):
    """
    Unit tests for EdicionLanding list and detail views.
    """
    @patch('apps.editions.views.edicion_landing_views.EdicionLanding.objects.using')
    def test_get_landing_editions(self, mock_using):
        mock_ed1 = MagicMock()
        mock_ed1.id = 1
        mock_ed1.imagen = "/media/landing_editions/xyz.jpg"
        mock_ed1.orden = 0

        # Mock sequence for objects querying
        mock_using.return_value.all.return_value.order_by.return_value = [mock_ed1]

        factory = APIRequestFactory()
        request = factory.get('/api/v1/public/editions-landing/')

        view = EdicionLandingListCreateView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['imagen'], "/media/landing_editions/xyz.jpg")
