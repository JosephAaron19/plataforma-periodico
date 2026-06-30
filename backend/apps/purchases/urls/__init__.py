from django.urls import path
from apps.purchases.views.purchase_views import PurchaseEditionView
from apps.purchases.views.mock_confirm_views import MockConfirmPaymentView
from apps.purchases.views.my_purchases_views import MyPurchasesView
from apps.purchases.views.submit_receipt_view import SubmitReceiptView
from apps.purchases.views.admin_purchases_views import (
    AdminPendingPurchasesView, AdminValidatePurchaseView, AdminSubscribersListView
)

urlpatterns = [
    # Purchase initiation endpoint
    path('editions/<int:edi_id>/purchase/', PurchaseEditionView.as_view(), name='purchase-edition'),
    # Mock payment confirmation (internal/dev only)
    path('payments/mock-confirm/', MockConfirmPaymentView.as_view(), name='mock-confirm-payment'),
    # Reader's purchase history
    path('my-purchases/', MyPurchasesView.as_view(), name='my-purchases'),
    # Submit payment receipt
    path('submit-receipt/', SubmitReceiptView.as_view(), name='submit-receipt'),
    # Admin endpoints
    path('admin/pending/', AdminPendingPurchasesView.as_view(), name='admin-pending'),
    path('admin/validate/', AdminValidatePurchaseView.as_view(), name='admin-validate'),
    path('admin/subscribers/', AdminSubscribersListView.as_view(), name='admin-subscribers'),
]
