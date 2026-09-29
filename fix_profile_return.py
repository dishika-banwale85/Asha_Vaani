with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the update_profile function - return statement is outside function
old = '''    )

return {
        "status": "success",
        "message": "Profile updated successfully"
    }

# Pydantic model for Profile Data'''

new = '''    )

    return {
        "status": "success",
        "message": "Profile updated successfully"
    }


# Pydantic model for Profile Data'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Fixed update_profile return')
else:
    print('Pattern not found')
    idx = content.find('return {\n        "status": "success",\n        "message": "Profile updated successfully"\n    }\n\n# Pydantic model')
    if idx >= 0:
        print(repr(content[idx-50:idx+150]))