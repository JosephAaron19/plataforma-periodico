from django.urls import path
from apps.payments.views.webhook_views import PaymentWebhookView

app_name = 'payments'

urlpatterns = [
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]
