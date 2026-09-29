"""
Security: PII Minimization & Hashing
Hash identifiers, encrypt sensitive fields, tokenization for analytics.
"""
from __future__ import annotations
import hashlib
import hmac
import secrets
import re
from dataclasses import dataclass
from typing import Optional, Any
from datetime import date, datetime


# ──────────────────────────────────────────────────────────────────────────────
# Hashing & Tokenization
# ──────────────────────────────────────────────────────────────────────────────

class PIDHasher:
    """
    Deterministic but salted hashing for patient identifiers.
    Same input → same hash (for linkage), but not reversible.
    """
    def __init__(self, pepper: Optional[bytes] = None):
        # Pepper stored in HSM/secret manager, not in DB
        self.pepper = pepper or __import__('os').environ.get("PII_PEPPER", "").encode()
        if not self.pepper:
            # Dev fallback
            self.pepper = hashlib.sha256(b"asha-vaani-pii-pepper-dev").digest()

    def hash_patient_id(self, *identifiers: str) -> str:
        """
        Create deterministic hash from patient identifiers.
        Use minimal set: e.g., (age, gender, village_hash, date_of_visit)
        """
        # Normalize
        parts = [self._normalize(p) for p in identifiers if p]
        combined = "|".join(parts)
        # HMAC with pepper
        return hmac.new(self.pepper, combined.encode(), hashlib.sha256).hexdigest()[:32]

    def hash_asha_id(self, worker_id: str) -> str:
        """Hash ASHA worker ID for analytics linkage."""
        return hmac.new(self.pepper, f"asha:{worker_id}".encode(), hashlib.sha256).hexdigest()[:24]

    def hash_village(self, village: str, district: str, state: str) -> str:
        """Hash location for geographic analytics without PII."""
        normalized = f"{state}|{district}|{village}".lower().strip()
        return hmac.new(self.pepper, f"village:{normalized}".encode(), hashlib.sha256).hexdigest()[:16]

    def _normalize(self, s: str) -> str:
        return re.sub(r'\s+', ' ', s.strip().lower())


class Tokenizer:
    """
    Reversible tokenization for fields that need re-identification by authorized roles.
    Uses AES-GCM via FieldEncryptor (see crypto.py).
    """
    def __init__(self, field_encryptor):
        self.fe = field_encryptor

    def tokenize(self, value: str, context: str) -> str:
        """Encrypt value → token (base64)."""
        return self.fe.encrypt(value, f"token:{context}")

    def detokenize(self, token: str, context: str) -> str:
        """Decrypt token → original value."""
        return self.fe.decrypt(token, f"token:{context}")


# ──────────────────────────────────────────────────────────────────────────────
# Patient Data Models (Minimal PII)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PatientRef:
    """
    Minimal patient reference for clinical workflows.
    NO direct identifiers - only derived/hashed fields.
    """
    patient_hash: str           # PIDHasher hash
    age_bucket: str             # "<1", "1-4", "5-14", "15-59", "60+"
    gender: str                 # "M" | "F" | "O"
    pregnant: bool
    village_hash: str           # Hashed location
    visit_date: date            # Date only, no time
    
    @classmethod
    def create(cls, hasher: PIDHasher, age: int, gender: str, pregnant: bool, 
               village: str, district: str, state: str, visit_date: date = None) -> PatientRef:
        return cls(
            patient_hash=hasher.hash_patient_id(str(age), gender, village, str(visit_date or date.today())),
            age_bucket=cls._age_bucket(age),
            gender=gender[0].upper() if gender else "O",
            pregnant=pregnant,
            village_hash=hasher.hash_village(village, district, state),
            visit_date=visit_date or date.today(),
        )

    @staticmethod
    def _age_bucket(age: int) -> str:
        if age < 1: return "<1"
        if age < 5: return "1-4"
        if age < 15: return "5-14"
        if age < 60: return "15-59"
        return "60+"


@dataclass
class TriageInput:
    """Input for offline/online triage - minimal fields."""
    patient_ref: PatientRef
    symptoms: list[str]              # Standardized symptom codes
    danger_signs: list[str]          # Standardized danger sign codes
    rdt_result: str                  # "neg", "pf", "pv", "mixed"
    asha_worker_hash: str            # Hashed ASHA ID
    
    def to_audit_payload(self) -> dict:
        """Safe payload for audit logging."""
        return {
            "patient_hash": self.patient_ref.patient_hash,
            "age_bucket": self.patient_ref.age_bucket,
            "gender": self.patient_ref.gender,
            "pregnant": self.patient_ref.pregnant,
            "village_hash": self.patient_ref.village_hash,
            "symptoms": self.symptoms,
            "danger_signs": self.danger_signs,
            "rdt_result": self.rdt_result,
            "asha_hash": self.asha_worker_hash,
        }


@dataclass
class ReferralRecord:
    """Referral with minimal PII."""
    id: str
    patient_hash: str
    asha_hash: str
    phc_id: str
    phc_name: str
    distance_km: float
    danger_signs: list[str]
    triage_summary: dict
    status: str  # "pending", "acknowledged", "completed"
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_audit_payload(self) -> dict:
        return {
            "id": self.id,
            "patient_hash": self.patient_hash,
            "asha_hash": self.asha_hash,
            "phc_id": self.phc_id,
            "distance_km": self.distance_km,
            "danger_signs": self.danger_signs,
            "status": self.status,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Data Retention & Deletion
# ──────────────────────────────────────────────────────────────────────────────

class RetentionPolicy:
    """Configurable retention policies per data category."""
    
    DEFAULT_POLICIES = {
        "chat_logs": 365,           # days
        "triage_logs": 1095,        # 3 years (clinical)
        "referral_logs": 2555,      # 7 years (medico-legal)
        "audit_logs": 2555,         # 7 years
        "voice_transcripts": 30,    # Short unless consented
        "analytics_events": 730,    # 2 years
        "consent_records": 2555,    # 7 years (legal)
        "profile_data": 365,        # 1 year after deactivation
    }
    
    def __init__(self, policies: dict = None):
        self.policies = {**self.DEFAULT_POLICIES, **(policies or {})}
    
    def get_retention_days(self, category: str) -> int:
        return self.policies.get(category, 365)
    
    def is_expired(self, category: str, created_at: datetime) -> bool:
        from datetime import timedelta
        days = self.get_retention_days(category)
        return datetime.utcnow() - created_at > timedelta(days=days)


class DataDeletionService:
    """Secure deletion with audit trail."""
    
    def __init__(self, db_conn, audit_logger, retention: RetentionPolicy):
        self.db = db_conn
        self.audit = audit_logger
        self.retention = retention
    
    def delete_expired(self, category: str, dry_run: bool = True) -> dict:
        """Delete expired records per retention policy."""
        # Implementation depends on table structure
        # This is a framework - actual queries in backend integration
        pass
    
    def delete_user_data(self, user_id: str, requester_id: str) -> dict:
        """Right to deletion (GDPR-style) with audit."""
        self.audit.log(
            __import__('security.audit').audit.AuditEventType.DATA_EXPORT,  # Reuse for deletion
            principal_id=requester_id,
            principal_role="admin",
            target_id=user_id,
            target_type="user_data",
            payload={"action": "deletion_request", "categories": ["all"]}
        )
        # Actual deletion logic here
        return {"status": "scheduled"}


# ──────────────────────────────────────────────────────────────────────────────
# Singleton Instances
# ──────────────────────────────────────────────────────────────────────────────

_pii_hasher: Optional[PIDHasher] = None
_tokenizer: Optional[Tokenizer] = None
_retention: Optional[RetentionPolicy] = None


def init_pii(pepper: Optional[bytes] = None, field_encryptor=None) -> tuple[PIDHasher, Tokenizer, RetentionPolicy]:
    global _pii_hasher, _tokenizer, _retention
    _pii_hasher = PIDHasher(pepper)
    _tokenizer = Tokenizer(field_encryptor) if field_encryptor else None
    _retention = RetentionPolicy()
    return _pii_hasher, _tokenizer, _retention


def get_pii_hasher() -> PIDHasher:
    if _pii_hasher is None:
        init_pii()
    return _pii_hasher


def get_tokenizer() -> Tokenizer:
    if _tokenizer is None:
        init_pii()
    return _tokenizer


def get_retention_policy() -> RetentionPolicy:
    if _retention is None:
        init_pii()
    return _retention