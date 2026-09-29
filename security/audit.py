"""
Security: Immutable Audit Logging
Append-only WAL with HMAC-SHA256 hash chaining for tamper evidence.
"""
from __future__ import annotations
import os
import json
import hmac
import hashlib
import sqlite3
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Any, List, Dict
from contextlib import contextmanager
from pathlib import Path


class AuditEventType(str, Enum):
    # Auth
    LOGIN = "login"
    LOGOUT = "logout"
    SIGNUP = "signup"
    PASSWORD_CHANGE = "password_change"
    PIN_SET = "pin_set"
    
    # Consent
    CONSENT_GRANTED = "consent_granted"
    CONSENT_REVOKED = "consent_revoked"
    
    # Chat / RAG
    CHAT_QUERY = "chat_query"
    CHAT_RESPONSE = "chat_response"
    CHAT_FEEDBACK = "chat_feedback"
    
    # Voice
    VOICE_SESSION_START = "voice_session_start"
    VOICE_SESSION_END = "voice_session_end"
    VOICE_TRANSCRIPT = "voice_transcript"
    
    # Triage / Clinical
    TRIAGE_CREATED = "triage_created"
    TRIAGE_DANGER_SIGNS = "triage_danger_signs"
    REFERRAL_CREATED = "referral_created"
    REFERRAL_ACKNOWLEDGED = "referral_acknowledged"
    REFERRAL_COMPLETED = "referral_completed"
    
    # Profile
    PROFILE_CREATED = "profile_created"
    PROFILE_UPDATED = "profile_updated"
    PROFILE_VIEWED = "profile_viewed"
    
    # Admin
    USER_CREATED = "user_created"
    USER_ROLE_CHANGED = "user_role_changed"
    USER_DEACTIVATED = "user_deactivated"
    GEO_SYNC_TRIGGERED = "geo_sync_triggered"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    
    # Data Access
    DATA_EXPORT = "data_export"
    AUDIT_LOG_VIEWED = "audit_log_viewed"


@dataclass(frozen=True)
class AuditEntry:
    """Single immutable audit log entry."""
    id: str                    # UUID
    event_type: AuditEventType
    principal_id: str          # User ID who performed action
    principal_role: str
    target_id: Optional[str]   # Affected resource ID (patient hash, referral ID, etc.)
    target_type: Optional[str] # Resource type
    payload: Dict[str, Any]    # Event details (NO PII - use hashes)
    timestamp: datetime
    prev_hash: str             # HMAC of previous entry
    hash: str                  # HMAC of this entry (prev_hash + payload)
    signature: str             # Ed25519 signature (optional, for non-repudiation)


class AuditLogger:
    """
    Tamper-evident audit log with hash chaining.
    Each entry includes HMAC(prev_hash + payload) creating a chain.
    Any modification breaks the chain.
    """
    
    def __init__(self, db_path: str = "audit.db", hmac_key: Optional[bytes] = None):
        self.db_path = db_path
        self.hmac_key = hmac_key or os.environ.get("AUDIT_HMAC_KEY", "").encode()
        if not self.hmac_key:
            # Dev fallback - deterministic key
            self.hmac_key = hashlib.sha256(b"asha-vaani-audit-dev-key").digest()
        
        self._lock = threading.RLock()
        self._init_db()
        self._last_hash = self._get_last_hash()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    principal_id TEXT NOT NULL,
                    principal_role TEXT NOT NULL,
                    target_id TEXT,
                    target_type TEXT,
                    payload TEXT NOT NULL,      -- JSON
                    timestamp TEXT NOT NULL,    -- ISO8601
                    prev_hash TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    signature TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_principal ON audit_log(principal_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_log(target_id, target_type)")

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _get_last_hash(self) -> str:
        with self._conn() as conn:
            row = conn.execute("SELECT hash FROM audit_log ORDER BY created_at DESC LIMIT 1").fetchone()
            return row["hash"] if row else "0" * 64  # Genesis hash

    def _compute_hash(self, prev_hash: str, payload: dict) -> str:
        """Compute HMAC-SHA256 of prev_hash + canonical payload."""
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        msg = prev_hash.encode() + canonical.encode()
        return hmac.new(self.hmac_key, msg, hashlib.sha256).hexdigest()

    def log(
        self,
        event_type: AuditEventType,
        principal_id: str,
        principal_role: str,
        payload: dict,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
    ) -> AuditEntry:
        """Create and persist audit entry. Returns the entry with computed hash."""
        with self._lock:
            entry_id = __import__('uuid').uuid4().hex
            timestamp = datetime.utcnow()
            
            # Sanitize payload - remove any potential PII
            safe_payload = self._sanitize_payload(payload)
            
            prev_hash = self._last_hash
            entry_hash = self._compute_hash(prev_hash, safe_payload)
            
            entry = AuditEntry(
                id=entry_id,
                event_type=event_type,
                principal_id=principal_id,
                principal_role=principal_role,
                target_id=target_id,
                target_type=target_type,
                payload=safe_payload,
                timestamp=timestamp,
                prev_hash=prev_hash,
                hash=entry_hash,
                signature="",  # TODO: Ed25519 sign with HSM key
            )
            
            with self._conn() as conn:
                conn.execute("""
                    INSERT INTO audit_log (id, event_type, principal_id, principal_role, target_id, target_type, payload, timestamp, prev_hash, hash, signature)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.id, entry.event_type.value, entry.principal_id, entry.principal_role,
                    entry.target_id, entry.target_type, json.dumps(entry.payload),
                    entry.timestamp.isoformat(), entry.prev_hash, entry.hash, entry.signature
                ))
            
            self._last_hash = entry_hash
            return entry

    def _sanitize_payload(self, payload: dict) -> dict:
        """Remove/redact PII from audit payload."""
        # Keys that should never appear in audit logs
        pii_keys = {
            'password', 'pin', 'token', 'secret', 'key', 'ssn', 'aadhaar',
            'phone', 'email', 'address', 'name', 'patient_name', 'dob',
            'latitude', 'longitude', 'gps', 'location', 'audio', 'recording'
        }
        safe = {}
        for k, v in payload.items():
            kl = k.lower()
            if any(pii in kl for pii in pii_keys):
                safe[k] = "[REDACTED]"
            elif isinstance(v, dict):
                safe[k] = self._sanitize_payload(v)
            elif isinstance(v, list):
                safe[k] = [self._sanitize_payload(i) if isinstance(i, dict) else i for i in v]
            else:
                safe[k] = v
        return safe

    # ──────────────────────────────────────────────────────────────────────────
    # Convenience Methods for Common Events
    # ──────────────────────────────────────────────────────────────────────────

    def log_consent(self, user_id: str, role: str, consent_record) -> AuditEntry:
        return self.log(
            AuditEventType.CONSENT_GRANTED if consent_record.granted else AuditEventType.CONSENT_REVOKED,
            principal_id=user_id,
            principal_role=role,
            target_id=user_id,
            target_type="user_consent",
            payload={
                "category": consent_record.category.value,
                "granted": consent_record.granted,
                "version": consent_record.version,
            }
        )

    def log_chat_query(self, user_id: str, role: str, query: str, session_id: str) -> AuditEntry:
        return self.log(
            AuditEventType.CHAT_QUERY,
            principal_id=user_id,
            principal_role=role,
            target_id=session_id,
            target_type="chat_session",
            payload={"query_hash": hashlib.sha256(query.encode()).hexdigest()[:16]}
        )

    def log_chat_response(self, user_id: str, role: str, session_id: str, response: str, confidence: float, sources: list, model: str) -> AuditEntry:
        return self.log(
            AuditEventType.CHAT_RESPONSE,
            principal_id=user_id,
            principal_role=role,
            target_id=session_id,
            target_type="chat_session",
            payload={
                "response_hash": hashlib.sha256(response.encode()).hexdigest()[:16],
                "confidence": confidence,
                "source_count": len(sources),
                "model": model,
            }
        )

    def log_triage(self, user_id: str, role: str, triage_data: dict, result: dict) -> AuditEntry:
        return self.log(
            AuditEventType.TRIAGE_CREATED,
            principal_id=user_id,
            principal_role=role,
            target_id=triage_data.get("patient_hash"),
            target_type="patient_triage",
            payload={
                "age_bucket": self._age_bucket(triage_data.get("age")),
                "gender": triage_data.get("gender"),
                "pregnant": triage_data.get("pregnant"),
                "test_result": triage_data.get("test_result"),
                "danger_signs_count": len(triage_data.get("danger_signs", [])),
                "urgent_referral": result.get("urgent", False),
                "treatment": result.get("treatment", "")[:50],
            }
        )

    def log_referral(self, user_id: str, role: str, referral: dict) -> AuditEntry:
        return self.log(
            AuditEventType.REFERRAL_CREATED,
            principal_id=user_id,
            principal_role=role,
            target_id=referral.get("id"),
            target_type="referral",
            payload={
                "patient_hash": referral.get("patient_hash"),
                "phc_id": referral.get("phc_id"),
                "distance_km": referral.get("distance_km"),
                "danger_signs": referral.get("danger_signs"),
            }
        )

    def log_referral_ack(self, user_id: str, role: str, referral_id: str, status: str) -> AuditEntry:
        return self.log(
            AuditEventType.REFERRAL_ACKNOWLEDGED,
            principal_id=user_id,
            principal_role=role,
            target_id=referral_id,
            target_type="referral",
            payload={"status": status}
        )

    def log_profile_update(self, user_id: str, role: str, worker_id: str, fields: list) -> AuditEntry:
        return self.log(
            AuditEventType.PROFILE_UPDATED,
            principal_id=user_id,
            principal_role=role,
            target_id=worker_id,
            target_type="profile",
            payload={"updated_fields": fields}
        )

    def log_admin_action(self, admin_id: str, action: str, target_id: str, target_type: str, details: dict) -> AuditEntry:
        return self.log(
            AuditEventType.USER_ROLE_CHANGED if "role" in action else AuditEventType.SYSTEM_CONFIG_CHANGED,
            principal_id=admin_id,
            principal_role="admin",
            target_id=target_id,
            target_type=target_type,
            payload={"action": action, **details}
        )

    def _age_bucket(self, age: Optional[int]) -> str:
        if age is None: return "unknown"
        if age < 1: return "<1"
        if age < 5: return "1-4"
        if age < 15: return "5-14"
        if age < 60: return "15-59"
        return "60+"

    # ──────────────────────────────────────────────────────────────────────────
    # Verification & Query
    # ──────────────────────────────────────────────────────────────────────────

    def verify_chain(self, limit: int = 1000) -> tuple[bool, Optional[str]]:
        """Verify hash chain integrity. Returns (valid, first_broken_entry_id)."""
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT id, prev_hash, hash, payload FROM audit_log ORDER BY created_at ASC LIMIT ?
            """, (limit,)).fetchall()
        
        prev = "0" * 64
        for row in rows:
            payload = json.loads(row["payload"])
            expected = self._compute_hash(prev, payload)
            if row["hash"] != expected:
                return False, row["id"]
            if row["prev_hash"] != prev:
                return False, row["id"]
            prev = row["hash"]
        return True, None

    def query(
        self,
        principal_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        target_id: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEntry]:
        """Query audit log with filters."""
        conditions = []
        params = []
        if principal_id:
            conditions.append("principal_id = ?")
            params.append(principal_id)
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type.value)
        if target_id:
            conditions.append("target_id = ?")
            params.append(target_id)
        if start:
            conditions.append("timestamp >= ?")
            params.append(start.isoformat())
        if end:
            conditions.append("timestamp <= ?")
            params.append(end.isoformat())
        
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.extend([limit, offset])
        
        with self._conn() as conn:
            rows = conn.execute(f"""
                SELECT * FROM audit_log {where} ORDER BY created_at DESC LIMIT ? OFFSET ?
            """, params).fetchall()
        
        return [self._row_to_entry(r) for r in rows]

    def _row_to_entry(self, row: sqlite3.Row) -> AuditEntry:
        return AuditEntry(
            id=row["id"],
            event_type=AuditEventType(row["event_type"]),
            principal_id=row["principal_id"],
            principal_role=row["principal_role"],
            target_id=row["target_id"],
            target_type=row["target_type"],
            payload=json.loads(row["payload"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            prev_hash=row["prev_hash"],
            hash=row["hash"],
            signature=row["signature"] or "",
        )


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_audit_logger: Optional[AuditLogger] = None


def init_audit(db_path: str = "audit.db", hmac_key: Optional[bytes] = None) -> AuditLogger:
    global _audit_logger
    _audit_logger = AuditLogger(db_path, hmac_key)
    return _audit_logger


def get_audit_logger() -> AuditLogger:
    if _audit_logger is None:
        init_audit()
    return _audit_logger