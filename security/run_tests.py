#!/usr/bin/env python
"""Run all security module tests"""
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from Asha_Vaani_main.security.test_crypto import main as test_crypto
from Asha_Vaani_main.security.test_pii import main as test_pii
from Asha_Vaani_main.security.test_consent import main as test_consent
from Asha_Vaani_main.security.test_audit import main as test_audit
from Asha_Vaani_main.security.test_rbac import main as test_rbac

print("=" * 50)
print("Running Security Module Tests")
print("=" * 50)

tests = [
    ("test_crypto", test_crypto),
    ("test_pii", test_pii),
    ("test_consent", test_consent),
    ("test_audit", test_audit),
    ("test_rbac", test_rbac),
]

for name, test_fn in tests:
    print(f"\n--- Running {name} ---")
    try:
        test_fn()
        print(f"✓ {name} passed")
    except Exception as e:
        print(f"FAILED: {name}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)