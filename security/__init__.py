"""
Security Package for ASHA VAANi
"""
from .crypto import (
    KeyManager, FieldEncryptor, ProfileEncryptor, ConsentEncryptor,
    EncryptedBlob, init_crypto, get_key_manager, get_field_encryptor,
    get_profile_encryptor, get_consent_encryptor,
)
from .consent import (
    ConsentCategory, ConsentFlags, ConsentRecord, ConsentManager,
    ConsentRequiredError, CURRENT_CONSENT_VERSION, CONSENT_FORM_CONTENT,
)
from .rbac import (
    Role, Permission, Principal, ROLE_PERMISSIONS,
    create_principal, compute_permissions,
    require_permission, require_role, require_worker_access,
    get_current_principal,
)
from .audit import (
    AuditEventType, AuditEntry, AuditLogger,
    init_audit, get_audit_logger,
)
from .pii import (
    PIDHasher, Tokenizer, PatientRef, TriageInput, ReferralRecord,
    RetentionPolicy, DataDeletionService,
    init_pii, get_pii_hasher, get_tokenizer, get_retention_policy,
)

__all__ = [
    # crypto
    "KeyManager", "FieldEncryptor", "ProfileEncryptor", "ConsentEncryptor",
    "EncryptedBlob", "init_crypto", "get_key_manager", "get_field_encryptor",
    "get_profile_encryptor", "get_consent_encryptor",
    # consent
    "ConsentCategory", "ConsentFlags", "ConsentRecord", "ConsentManager",
    "ConsentRequiredError", "CURRENT_CONSENT_VERSION", "CONSENT_FORM_CONTENT",
    # rbac
    "Role", "Permission", "Principal", "ROLE_PERMISSIONS",
    "create_principal", "compute_permissions",
    "require_permission", "require_role", "require_worker_access",
    "get_current_principal",
    # audit
    "AuditEventType", "AuditEntry", "AuditLogger",
    "init_audit", "get_audit_logger",
    # pii
    "PIDHasher", "Tokenizer", "PatientRef", "TriageInput", "ReferralRecord",
    "RetentionPolicy", "DataDeletionService",
    "init_pii", "get_pii_hasher", "get_tokenizer", "get_retention_policy",
]