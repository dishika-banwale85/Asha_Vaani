"""Quick test for consent module"""
from security.consent import ConsentFlags, ConsentCategory, ConsentManager, CURRENT_CONSENT_VERSION, CONSENT_FORM_CONTENT


def main():
    # Test ConsentFlags
    flags = ConsentFlags(
        patient_data=True,
        audio_recording=False,
        analytics=True,
        location_tracking=True,
        referral_sharing=True,
        version=CURRENT_CONSENT_VERSION
    )

    print(f"Flags: {flags.to_dict()}")

    # Test validation using ConsentManager
    mgr = ConsentManager(None, None)  # encryptor, audit not needed for this test
    valid, missing = mgr.validate_consent(flags)
    print(f"Valid: {valid}, Missing: {missing}")

    # Test category access
    assert flags.get_category(ConsentCategory.PATIENT_DATA) == True
    assert flags.get_category(ConsentCategory.AUDIO_RECORDING) == False
    flags.set_category(ConsentCategory.AUDIO_RECORDING, True)
    assert flags.get_category(ConsentCategory.AUDIO_RECORDING) == True
    print("✓ Category get/set works")

    # Test consent form content
    print(f"Consent form version: {CONSENT_FORM_CONTENT['version']}")
    print(f"Categories: {len(CONSENT_FORM_CONTENT['categories'])}")
    for cat in CONSENT_FORM_CONTENT['categories']:
        print(f"  - {cat['id']}: required={cat['required']}")

    print("\nAll consent tests passed!")


if __name__ == "__main__":
    main()