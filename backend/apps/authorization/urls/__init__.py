from django.urls import path
from apps.authorization.views import (
    CompanyInvitationListCreateView,
    CompanyInvitationResendView,
    CompanyInvitationRevokeView,
    CompanyMemberListView,
    CompanyMemberDetailView,
    CompanyMemberSuspendView,
    CompanyMemberReactivateView,
    CompanyRoleListView,
    CompanyPermissionListView,
    MemberRoleListAssignView,
    MemberRoleFinalizeView,
    MemberRoleSetPrimaryView,
    MemberEffectivePermissionListView,
    MemberPermissionGrantView,
    MemberPermissionRevokeView,
    MemberPermissionRemoveExceptionView
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

    # Roles and Permissions management
    path('roles/', CompanyRoleListView.as_view(), name='company-role-list'),
    path('permissions/', CompanyPermissionListView.as_view(), name='company-permission-list'),
    path('members/<int:uep_id>/roles/', MemberRoleListAssignView.as_view(), name='member-role-list-assign'),
    path('members/<int:uep_id>/roles/<int:assignment_id>/finalize/', MemberRoleFinalizeView.as_view(), name='member-role-finalize'),
    path('members/<int:uep_id>/roles/<int:assignment_id>/set-primary/', MemberRoleSetPrimaryView.as_view(), name='member-role-set-primary'),
    path('members/<int:uep_id>/permissions/', MemberEffectivePermissionListView.as_view(), name='member-effective-permissions'),
    path('members/<int:uep_id>/permissions/grant/', MemberPermissionGrantView.as_view(), name='member-permission-grant'),
    path('members/<int:uep_id>/permissions/revoke/', MemberPermissionRevokeView.as_view(), name='member-permission-revoke'),
    path('members/<int:uep_id>/permissions/<str:permission_code>/exception/', MemberPermissionRemoveExceptionView.as_view(), name='member-permission-remove-exception'),
]

