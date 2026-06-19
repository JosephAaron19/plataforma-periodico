from django.urls import path
from apps.accounts.views import (
    RegisterView, VerifyEmailView, ResendVerificationView,
    LoginView, TokenRefreshView, LogoutView
)
from apps.authorization.views import InvitationAcceptView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('invitations/accept/', InvitationAcceptView.as_view(), name='invitation-accept'),
]


