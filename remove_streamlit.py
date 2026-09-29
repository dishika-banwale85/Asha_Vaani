with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the unused streamlit import
old = '''from dotenv import load_dotenv
from streamlit import user  # <-- 1. Import the library
import requests'''

new = '''from dotenv import load_dotenv
import requests'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Removed unused streamlit import')
else:
    print('Pattern not found')