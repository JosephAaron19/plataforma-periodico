from django.urls import path
from apps.authorization.views import (
    CompanyInvitationListCreateView,
    CompanyInvitationResendView,
    CompanyInvitationRevokeView,
    CompanyMemberListView,
    CompanyMemberDetailView,
    CompanyMemberSuspendView,
    CompanyMemberReactivateView
)

urlpatterns = [
    # Invitations
    path('invitations/', CompanyInvitationListCreateView.as_view(), name='company-invitation-list-create'),
    path('invitations/<uuid:invitation_id>/resend/', CompanyInvitationResendView.as_view(), name='company-invitation-resend'),
    path('invitations/<uuid:invitation_id>/revoke/', CompanyInvitationRevokeView.as_view(), name='company-invitation-revoke'),
    
    # Members
    path('members/', CompanyMemberListView.as_view(), name='company-member-list'),
    path('members/<int:uep_id>/', CompanyMemberDetailView.as_view(), name='company-member-detail'),
    path('members/<int:uep_id>/suspend/', CompanyMemberSuspendView.as_view(), name='company-member-suspend'),
    path('members/<int:uep_id>/reactivate/', CompanyMemberReactivateView.as_view(), name='company-member-reactivate'),
]
