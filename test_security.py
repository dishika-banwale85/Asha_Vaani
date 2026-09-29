import requests
import json
import time

BASE = 'http://127.0.0.1:8000'

# Use timestamp for unique username
username = f'testuser_{int(time.time())}'

# Test 1: Unauthorized /chat
print('=== Test 1: Unauthorized /chat ===')
r = requests.post(BASE + '/chat', json={'message': 'test'})
print(f'Status: {r.status_code}')
print(f'Response: {r.json()}')
print()

# Test 2: Signup (new user)
print('=== Test 2: Signup ===')
r = requests.post(BASE + '/signup', json={'username': username, 'password': 'testpass'})
print(f'Status: {r.status_code}')
if r.status_code == 200:
    token = r.json()['token']
    print(f'Token: {token[:50]}...')
    print()

    # Test 3: Authorized /chat (should fail with consent_required)
    print('=== Test 3: Authorized /chat (no consent) ===')
    r = requests.post(BASE + '/chat', 
        headers={'Authorization': f'Bearer {token}'},
        json={'message': 'What is malaria?', 'history': []}
    )
    print(f'Status: {r.status_code}')
    print(f'Response: {json.dumps(r.json(), indent=2)}')
    print()

    # Test 4: Get consent form
    print('=== Test 4: Get consent form ===')
    r = requests.get(BASE + '/api/consent', headers={'Authorization': f'Bearer {token}'})
    print(f'Status: {r.status_code}')
    print(f'Response: {json.dumps(r.json(), indent=2)}')
    print()

    # Test 5: Accept consent
    print('=== Test 5: Accept consent ===')
    r = requests.post(BASE + '/api/consent', 
        headers={'Authorization': f'Bearer {token}'},
        json={
            'patient_data': True,
            'audio_recording': False,
            'analytics': True,
            'location_tracking': True,
            'referral_sharing': True
        }
    )
    print(f'Status: {r.status_code}')
    print(f'Response: {r.json()}')
    print()

    # Test 6: Authorized /chat (with consent)
    print('=== Test 6: Authorized /chat (with consent) ===')
    r = requests.post(BASE + '/chat', 
        headers={'Authorization': f'Bearer {token}'},
        json={'message': 'What is malaria?', 'history': []}
    )
    print(f'Status: {r.status_code}')
    result = r.json()
    filtered = {k: v for k, v in result.items() if k != 'response'}
    print(f'Response metadata: {json.dumps(filtered, indent=2)}')
    if 'response' in result:
        print(f'Response text (first 200 chars): {result["response"][:200]}')
    print()

    # Test 7: Get own profile
    print('=== Test 7: Get own profile ===')
    r = requests.get(BASE + f'/api/profile/{username}', headers={'Authorization': f'Bearer {token}'})
    print(f'Status: {r.status_code}')
    print(f'Response: {r.json()}')
    print()

    # Test 8: Try to access another user's profile (should be 403)
    print('=== Test 8: Access another user profile (should be 403) ===')
    r = requests.get(BASE + '/api/profile/otheruser', headers={'Authorization': f'Bearer {token}'})
    print(f'Status: {r.status_code}')
    print(f'Response: {r.json()}')
    print()

    # Test 9: Verify audit chain
    print('=== Test 9: Verify audit chain (admin only - should be 403 for asha) ===')
    r = requests.get(BASE + '/api/admin/audit/verify', headers={'Authorization': f'Bearer {token}'})
    print(f'Status: {r.status_code}')
    print(f'Response: {r.json()}')
else:
    print(f'Signup failed: {r.json()}')