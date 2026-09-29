"""
Security: Role-Based Access Control (RBAC)
Roles: asha, supervisor, admin
Permissions scoped to resources and actions.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Optional, Set, TYPE_CHECKING
from fastapi import HTTPException, Depends

if TYPE_CHECKING:
    from backend import get_current_user  # Forward reference for type hints


class Role(str, Enum):
    ASHA = "asha"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class Permission(str, Enum):
    # Chat / RAG
    CHAT_QUERY = "chat:query"
    CHAT_HISTORY_OWN = "chat:history:own"
    CHAT_HISTORY_ALL = "chat:history:all"
    CHAT_FEEDBACK = "chat:feedback"
    
    # Voice
    VOICE_STREAM = "voice:stream"
    VOICE_HISTORY = "voice:history"
    
    # Offline Triage
    TRIAGE_CREATE = "triage:create"
    TRIAGE_HISTORY_OWN = "triage:history:own"
    TRIAGE_HISTORY_ALL = "triage:history:all"
    
    # Referrals
    REFERRAL_CREATE = "referral:create"
    REFERRAL_VIEW_OWN = "referral:view:own"
    REFERRAL_VIEW_ALL = "referral:view:all"
    REFERRAL_ACKNOWLEDGE = "referral:acknowledge"  # Supervisor/PHC
    REFERRAL_EXPORT = "referral:export"
    
    # Profile
    PROFILE_VIEW_OWN = "profile:view:own"
    PROFILE_EDIT_OWN = "profile:edit:own"
    PROFILE_VIEW_ALL = "profile:view:all"
    PROFILE_EDIT_ALL = "profile:edit:all"
    
    # Admin
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG = "system:config"
    AUDIT_VIEW = "audit:view"
    AUDIT_EXPORT = "audit:export"
    GEO_SYNC = "geo:sync"
    
    # Consent
    CONSENT_VIEW_OWN = "consent:view:own"
    CONSENT_EDIT_OWN = "consent:edit:own"


# Role → Permission mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ASHA: {
        Permission.CHAT_QUERY,
        Permission.CHAT_HISTORY_OWN,
        Permission.CHAT_FEEDBACK,
        Permission.VOICE_STREAM,
        Permission.VOICE_HISTORY,
        Permission.TRIAGE_CREATE,
        Permission.TRIAGE_HISTORY_OWN,
        Permission.REFERRAL_CREATE,
        Permission.REFERRAL_VIEW_OWN,
        Permission.PROFILE_VIEW_OWN,
        Permission.PROFILE_EDIT_OWN,
        Permission.CONSENT_VIEW_OWN,
        Permission.CONSENT_EDIT_OWN,
    },
    Role.SUPERVISOR: {
        # Inherits ASHA permissions
        Permission.CHAT_QUERY,
        Permission.CHAT_HISTORY_OWN,
        Permission.CHAT_HISTORY_ALL,
        Permission.CHAT_FEEDBACK,
        Permission.VOICE_STREAM,
        Permission.VOICE_HISTORY,
        Permission.TRIAGE_CREATE,
        Permission.TRIAGE_HISTORY_OWN,
        Permission.TRIAGE_HISTORY_ALL,
        Permission.REFERRAL_CREATE,
        Permission.REFERRAL_VIEW_OWN,
        Permission.REFERRAL_VIEW_ALL,
        Permission.REFERRAL_ACKNOWLEDGE,
        Permission.REFERRAL_EXPORT,
        Permission.PROFILE_VIEW_OWN,
        Permission.PROFILE_EDIT_OWN,
        Permission.PROFILE_VIEW_ALL,
        Permission.CONSENT_VIEW_OWN,
        Permission.CONSENT_EDIT_OWN,
        Permission.AUDIT_VIEW,
    },
    Role.ADMIN: set(Permission),  # All permissions
}


@dataclass(frozen=True)
class Principal:
    """Authenticated user with roles and scoped access."""
    user_id: str
    username: str
    roles: frozenset[Role]
    worker_id: Optional[str] = None      # For ASHA: their worker ID
    supervised_workers: frozenset[str] = frozenset()  # For supervisor: worker IDs they oversee
    permissions: frozenset[Permission] = frozenset()

    def has_permission(self, perm: Permission) -> bool:
        return perm in self.permissions

    def has_role(self, role: Role) -> bool:
        return role in self.roles

    def can_access_worker(self, worker_id: str) -> bool:
        """Check if principal can access data for given worker."""
        if self.has_role(Role.ADMIN):
            return True
        if self.has_role(Role.SUPERVISOR):
            return worker_id in self.supervised_workers
        if self.has_role(Role.ASHA):
            return self.worker_id == worker_id
        return False


def compute_permissions(roles: Set[Role]) -> Set[Permission]:
    """Aggregate permissions from roles."""
    perms = set()
    for role in roles:
        perms.update(ROLE_PERMISSIONS.get(role, set()))
    return perms


def create_principal(user_row: dict, profile_row: Optional[dict] = None) -> Principal:
    """Create Principal from DB rows."""
    role_str = user_row.get("role", "asha")
    try:
        role = Role(role_str)
    except ValueError:
        role = Role.ASHA
    
    roles = {role}
    permissions = compute_permissions(roles)
    
    worker_id = profile_row.get("worker_id") if profile_row else None
    supervised = frozenset(profile_row.get("supervised_workers", "").split(",")) if profile_row and profile_row.get("supervised_workers") else frozenset()
    
    return Principal(
        user_id=str(user_row["id"]),
        username=user_row["username"],
        roles=frozenset(roles),
        worker_id=worker_id,
        supervised_workers=supervised,
        permissions=frozenset(permissions),
    )


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI Dependencies (to be implemented in backend integration)
# ──────────────────────────────────────────────────────────────────────────────

# Placeholder - actual implementation in backend/main.py
async def get_current_principal() -> Principal:
    """FastAPI dependency: get current authenticated principal.
    Override this in backend with actual auth logic."""
    raise NotImplementedError("Implement in backend integration")


def require_permission(perm: Permission):
    """FastAPI dependency: require specific permission."""
    async def check(principal: Principal = Depends(get_current_principal)):
        if not principal.has_permission(perm):
            raise HTTPException(403, f"Permission denied: {perm.value}")
        return principal
    return check


def require_role(role: Role):
    """FastAPI dependency: require specific role."""
    async def check(principal: Principal = Depends(get_current_principal)):
        if not principal.has_role(role):
            raise HTTPException(403, f"Role required: {role.value}")
        return principal
    return check


def require_worker_access(worker_id_param: str = "worker_id"):
    """FastAPI dependency: require access to specific worker's data."""
    async def check(principal: Principal = Depends(get_current_principal), worker_id: str = None):
        # worker_id will be extracted from path/query params
        if worker_id is None:
            # Try to get from request - placeholder, actual implementation in backend
            pass
        if not principal.can_access_worker(worker_id):
            raise HTTPException(403, "Access denied to this worker's data")
        return principal
    return check


# ──────────────────────────────────────────────────────────────────────────────
# Convenience Decorators
# ──────────────────────────────────────────────────────────────────────────────

def permission_required(perm: Permission):
    """Decorator for internal functions (non-FastAPI)."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Assumes first arg is principal or principal in kwargs
            principal = kwargs.get('principal') or (args[0] if args and isinstance(args[0], Principal) else None)
            if not principal or not principal.has_permission(perm):
                raise PermissionError(f"Permission denied: {perm.value}")
            return func(*args, **kwargs)
        return wrapper
    return decorator