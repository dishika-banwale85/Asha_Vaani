"""Quick test for crypto module"""
import os
os.environ["MASTER_ENCRYPTION_KEY"] = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="  # base64 of 32 bytes

from security.crypto import init_crypto, get_field_encryptor, get_profile_encryptor


def main():
    init_crypto()
    fe = get_field_encryptor()
    pe = get_profile_encryptor()

    # Test field encryption
    ctx = "test-field"
    original = "sensitive patient data: age=25, gender=F, pregnant=True"
    encrypted = fe.encrypt(original, ctx)
    print(f"Encrypted: {encrypted[:50]}...")

    decrypted = fe.decrypt(encrypted, ctx)
    print(f"Decrypted: {decrypted}")
    assert decrypted == original, "Field encrypt/decrypt failed"
    print("✓ Field encryption works")

    # Test profile encryption
    profile = {"name": "Sunita Devi", "village": "Rampur", "sub_center": "SC-Alpha", "phone": "9876543210"}
    enc_profile = pe.encrypt(profile)
    print(f"Encrypted profile: {enc_profile[:50]}...")

    dec_profile = pe.decrypt(enc_profile)
    print(f"Decrypted profile: {dec_profile}")
    assert dec_profile == profile, "Profile encrypt/decrypt failed"
    print("✓ Profile encryption works")

    print("\nAll crypto tests passed!")


if __name__ == "__main__":
    main()