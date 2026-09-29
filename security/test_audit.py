"""Quick test for audit module"""
import os
os.environ["AUDIT_HMAC_KEY"] = "dGVzdC1hdWRpdC1obWFjLWtleS10aXJ0eS1ieXRlcw=="  # base64 of 32 bytes

from security.audit import AuditLogger, AuditEventType


def main():
    # Clean up any existing test DB
    if os.path.exists("test_audit.db"):
        os.remove("test_audit.db")

    audit = AuditLogger("test_audit.db")

    # Log some events
    entry1 = audit.log(
        AuditEventType.LOGIN,
        principal_id="user-123",
        principal_role="asha",
        payload={"method": "password", "success": True}
    )
    print(f"Entry 1: {entry1.id}, hash: {entry1.hash[:16]}...")

    entry2 = audit.log(
        AuditEventType.CHAT_QUERY,
        principal_id="user-123",
        principal_role="asha",
        payload={"query_hash": "abc123", "session_id": "sess-456"},
        target_id="sess-456",
        target_type="chat_session"
    )
    print(f"Entry 2: {entry2.id}, hash: {entry2.hash[:16]}...")

    entry3 = audit.log(
        AuditEventType.REFERRAL_CREATED,
        principal_id="user-123",
        principal_role="asha",
        payload={"phc_id": "PHC-001", "distance_km": 5.2, "danger_signs": ["vomiting"]},
        target_id="ref-789",
        target_type="referral"
    )
    print(f"Entry 3: {entry3.id}, hash: {entry3.hash[:16]}...")

    # Verify chain
    valid, broken_id = audit.verify_chain()
    print(f"Chain valid: {valid}")
    assert valid, "Chain should be valid"

    # Query
    entries = audit.query(principal_id="user-123", limit=10)
    print(f"Queried {len(entries)} entries")
    assert len(entries) == 3

    # Test sanitization
    entry_pii = audit.log(
        AuditEventType.PROFILE_UPDATED,
        principal_id="user-123",
        principal_role="asha",
        payload={"name": "Sunita Devi", "phone": "9876543210", "age": 35, "updated_fields": ["phone"]},
        target_id="ASHA-001",
        target_type="profile"
    )
    print(f"PIE entry payload: {entry_pii.payload}")
    assert entry_pii.payload["name"] == "[REDACTED]"
    assert entry_pii.payload["phone"] == "[REDACTED]"
    assert entry_pii.payload["age"] == 35  # age is not PII
    print("✓ PII sanitization works")

    # Cleanup
    os.remove("test_audit.db")
    print("\nAll audit tests passed!")


if __name__ == "__main__":
    main()