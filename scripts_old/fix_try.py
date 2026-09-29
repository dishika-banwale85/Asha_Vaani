with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the duplicate try:
old = '''    )

    try:try:
        # Ensure you have 'import os\''''

new = '''    )

    try:
        # Ensure you have 'import os\''''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed duplicate try:')
else:
    print('Pattern not found')