with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation - the return statement has 8 spaces instead of 4
old = '''        return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm="HS256"
    )'''

new = '''    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm="HS256"
    )'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed indentation')
else:
    print('Pattern not found')
    # Debug
    idx = content.find('return jwt.encode')
    if idx >= 0:
        print(repr(content[idx:idx+150]))