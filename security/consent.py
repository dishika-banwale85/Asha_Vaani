"""
Security: Consent Management
Explicit, granular, versioned consent for data processing categories.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class ConsentCategory(str, Enum):
    """Categories of data processing requiring consent."""
    PATIENT_DATA = "patient_data"          # Patient demographics, symptoms, triage
    AUDIO_RECORDING = "audio_recording"    # Voice input recordings
    ANALYTICS = "analytics"                # Usage analytics, model improvement
    LOCATION_TRACKING = "location_tracking" # GPS for PHC routing
    REFERRAL_SHARING = "referral_sharing"  # Sharing referral with PHC/supervisor


@dataclass(frozen=True)
class ConsentRecord:
    """Single consent decision."""
    category: ConsentCategory
    granted: bool
    timestamp: datetime
    version: int                          # Consent form version
    ip_hash: Optional[str] = None         # Hashed IP for audit
    user_agent: Optional[str] = None


@dataclass
class ConsentFlags:
    """Current consent state for a user."""
    patient_data: bool = False
    audio_recording: bool = False
    analytics: bool = False
    location_tracking: bool = False
    referral_sharing: bool = False
    version: int = 1
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "patient_data": self.patient_data,
            "audio_recording": self.audio_recording,
            "analytics": self.analytics,
            "location_tracking": self.location_tracking,
            "referral_sharing": self.referral_sharing,
            "version": self.version,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ConsentFlags:
        return cls(
            patient_data=data.get("patient_data", False),
            audio_recording=data.get("audio_recording", False),
            analytics=data.get("analytics", False),
            location_tracking=data.get("location_tracking", False),
            referral_sharing=data.get("referral_sharing", False),
            version=data.get("version", 1),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
        )

    def get_category(self, cat: ConsentCategory) -> bool:
        return getattr(self, cat.value, False)

    def set_category(self, cat: ConsentCategory, granted: bool) -> None:
        setattr(self, cat.value, granted)
        self.updated_at = datetime.utcnow()

    def all_granted(self) -> bool:
        return all([
            self.patient_data,
            self.audio_recording,
            self.analytics,
            self.location_tracking,
            self.referral_sharing,
        ])


# Current consent form version (increment when fields change)
CURRENT_CONSENT_VERSION = 1

CONSENT_FORM_CONTENT = {
    "version": CURRENT_CONSENT_VERSION,
    "categories": [
        {
            "id": ConsentCategory.PATIENT_DATA.value,
            "title": "Patient Health Data",
            "description": "Store and process patient demographics (age, gender, pregnancy), symptoms, RDT results, and triage outcomes for clinical decision support.",
            "required": True,  # Core functionality
            "retention_days": 365,
        },
        {
            "id": ConsentCategory.AUDIO_RECORDING.value,
            "title": "Voice Recordings",
            "description": "Record voice inputs for speech-to-text processing. Audio is transcribed and discarded unless you opt-in to store for quality improvement.",
            "required": False,
            "retention_days": 30,
        },
        {
            "id": ConsentCategory.ANALYTICS.value,
            "title": "Usage Analytics",
            "description": "Anonymous usage patterns to improve the system. No patient identifiers included.",
            "required": False,
            "retention_days": 730,
        },
        {
            "id": ConsentCategory.LOCATION_TRACKING.value,
            "title": "Location for PHC Routing",
            "description": "Use GPS to find nearest Primary Health Center for referrals. Location not stored after routing.",
            "required": False,
            "retention_days": 1,
        },
        {
            "id": ConsentCategory.REFERRAL_SHARING.value,
            "title": "Referral Data Sharing",
            "description": "Share referral details (danger signs, patient info) with the receiving PHC and your supervisor for continuity of care.",
            "required": True,  # Required for referral workflow
            "retention_days": 365,
        },
    ],
    "withdrawal_info": "You can withdraw consent anytime in Settings. Withdrawing required consents may limit functionality.",
}


class ConsentManager:
    """Manage consent flow, validation, and audit trail."""
    
    def __init__(self, encryptor, audit_logger):
        self.encryptor = encryptor
        self.audit = audit_logger

    def get_form(self) -> dict:
        """Return current consent form for UI."""
        return CONSENT_FORM_CONTENT

    def validate_consent(self, flags: ConsentFlags) -> tuple[bool, list[str]]:
        """Check if required consents are granted."""
        missing = []
        for cat_info in CONSENT_FORM_CONTENT["categories"]:
            if cat_info["required"] and not flags.get_category(ConsentCategory(cat_info["id"])):
                missing.append(cat_info["title"])
        return len(missing) == 0, missing

    def record_consent(self, user_id: str, flags: ConsentFlags, ip_hash: str = None, ua: str = None) -> list[ConsentRecord]:
        """Record consent decisions with audit trail."""
        records = []
        for cat in ConsentCategory:
            granted = flags.get_category(cat)
            record = ConsentRecord(
                category=cat,
                granted=granted,
                timestamp=datetime.utcnow(),
                version=flags.version,
                ip_hash=ip_hash,
                user_agent=ua,
            )
            records.append(record)
            # Audit log
            self.audit.log_consent(user_id, "asha", record)
        return records

    def has_consent(self, flags: ConsentFlags, category: ConsentCategory) -> bool:
        """Check if user has granted consent for category."""
        return flags.get_category(category)

    def require_consent(self, flags: ConsentFlags, category: ConsentCategory, action: str) -> None:
        """Raise if consent not granted for required action."""
        if not self.has_consent(flags, category):
            raise ConsentRequiredError(category, action)


class ConsentRequiredError(Exception):
    def __init__(self, category: ConsentCategory, action: str):
        self.category = category
        self.action = action
        super().__init__(f"Consent required for {category.value} to {action}")


# Consent validation decorators for API endpoints
def require_consent(category: ConsentCategory, action: str):
    """FastAPI dependency to enforce consent. Implement in backend integration."""
    def _placeholder():
        raise NotImplementedError("Implement in backend integration")
    return _placeholder