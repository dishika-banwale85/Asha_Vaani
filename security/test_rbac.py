"""Quick test for RBAC module"""
from security.rbac import Role, Permission, Principal, create_principal, compute_permissions, ROLE_PERMISSIONS


def main():
    # Test role permissions
    asha_perms = ROLE_PERMISSIONS[Role.ASHA]
    sup_perms = ROLE_PERMISSIONS[Role.SUPERVISOR]
    admin_perms = ROLE_PERMISSIONS[Role.ADMIN]

    print(f"ASHA permissions: {len(asha_perms)}")
    print(f"Supervisor permissions: {len(sup_perms)}")
    print(f"Admin permissions: {len(admin_perms)}")

    # Admin should have all permissions
    assert len(admin_perms) == len(Permission)
    print("✓ Admin has all permissions")

    # Supervisor should have ASHA + more
    assert asha_perms.issubset(sup_perms)
    print("✓ Supervisor inherits ASHA permissions")

    # Test principal creation
    user_row = {"id": 1, "username": "sunita", "role": "asha"}
    profile_row = {"worker_id": "ASHA-001", "supervised_workers": ""}
    principal = create_principal(user_row, profile_row)

    print(f"Principal: {principal.username}, roles: {[r.value for r in principal.roles]}")
    print(f"Worker ID: {principal.worker_id}")
    print(f"Permissions: {len(principal.permissions)}")

    assert principal.has_permission(Permission.CHAT_QUERY)
    assert principal.has_permission(Permission.TRIAGE_CREATE)
    assert not principal.has_permission(Permission.USER_MANAGE)
    assert principal.has_role(Role.ASHA)
    print("✓ ASHA principal permissions correct")

    # Test supervisor principal
    sup_user = {"id": 2, "username": "supervisor1", "role": "supervisor"}
    sup_profile = {"worker_id": "SUP-001", "supervised_workers": "ASHA-001,ASHA-002,ASHA-003"}
    sup_principal = create_principal(sup_user, sup_profile)

    assert sup_principal.has_permission(Permission.REFERRAL_VIEW_ALL)
    assert sup_principal.has_permission(Permission.TRIAGE_HISTORY_ALL)
    assert sup_principal.can_access_worker("ASHA-001")
    assert sup_principal.can_access_worker("ASHA-002")
    assert not sup_principal.can_access_worker("ASHA-999")
    print("✓ Supervisor principal permissions correct")

    # Test admin principal
    admin_user = {"id": 3, "username": "admin1", "role": "admin"}
    admin_profile = {"worker_id": None, "supervised_workers": ""}
    admin_principal = create_principal(admin_user, admin_profile)

    assert admin_principal.has_permission(Permission.USER_MANAGE)
    assert admin_principal.has_permission(Permission.AUDIT_EXPORT)
    assert admin_principal.can_access_worker("any-worker")
    print("✓ Admin principal permissions correct")

    print("\nAll RBAC tests passed!")


if __name__ == "__main__":
    main()