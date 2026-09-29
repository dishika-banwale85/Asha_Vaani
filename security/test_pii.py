"""Quick test for PII module"""
from security.pii import PIDHasher, PatientRef, TriageInput
from datetime import date


def main():
    # Use a test pepper
    pepper = b"test-pepper-32-bytes-long-secret"
    hasher = PIDHasher(pepper)

    # Test patient hashing
    patient_hash = hasher.hash_patient_id("25", "F", "Rampur", "2024-01-15")
    print(f"Patient hash: {patient_hash}")
    assert len(patient_hash) == 32, "Hash should be 32 chars"

    # Test ASHA hashing
    asha_hash = hasher.hash_asha_id("ASHA-001")
    print(f"ASHA hash: {asha_hash}")
    assert len(asha_hash) == 24, "ASHA hash should be 24 chars"

    # Test village hashing
    village_hash = hasher.hash_village("Rampur", "Bhopal", "Madhya Pradesh")
    print(f"Village hash: {village_hash}")
    assert len(village_hash) == 16, "Village hash should be 16 chars"

    # Test deterministic - same input = same hash
    patient_hash2 = hasher.hash_patient_id("25", "F", "Rampur", "2024-01-15")
    assert patient_hash == patient_hash2, "Hash should be deterministic"
    print("✓ Hashing is deterministic")

    # Test PatientRef
    pref = PatientRef.create(
        hasher, age=25, gender="Female", pregnant=False,
        village="Rampur", district="Bhopal", state="Madhya Pradesh",
        visit_date=date(2024, 1, 15)
    )
    print(f"PatientRef: {pref}")
    assert pref.age_bucket == "15-59"
    assert pref.gender == "F"
    assert not pref.pregnant
    print("✓ PatientRef creation works")

    # Test TriageInput
    triage = TriageInput(
        patient_ref=pref,
        symptoms=["fever", "chills"],
        danger_signs=[],
        rdt_result="pf",
        asha_worker_hash=asha_hash
    )
    audit_payload = triage.to_audit_payload()
    print(f"Audit payload keys: {list(audit_payload.keys())}")
    assert "patient_hash" in audit_payload
    assert "symptoms" in audit_payload
    print("✓ TriageInput audit payload works")

    print("\nAll PII tests passed!")


if __name__ == "__main__":
    main()