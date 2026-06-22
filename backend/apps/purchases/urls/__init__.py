from django.urls import path
from apps.purchases.views.purchase_views import PurchaseEditionView
from apps.purchases.views.mock_confirm_views import MockConfirmPaymentView
from apps.purchases.views.my_purchases_views import MyPurchasesView

urlpatterns = [
    # Purchase initiation endpoint
    path('editions/<int:edi_id>/purchase/', PurchaseEditionView.as_view(), name='purchase-edition'),
    # Mock payment confirmation (internal/dev only)
    path('payments/mock-confirm/', MockConfirmPaymentView.as_view(), name='mock-confirm-payment'),
    # Reader's purchase history
    path('my-purchases/', MyPurchasesView.as_view(), name='my-purchases'),
]
