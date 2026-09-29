with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update create_access_token to include role
old = '''def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=2)
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm="HS256"
    )'''

new = '''def create_access_token(username: str, role: str = "asha") -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=2)
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm="HS256"
    )'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: create_access_token updated')
else:
    print('OLD STRING NOT FOUND')