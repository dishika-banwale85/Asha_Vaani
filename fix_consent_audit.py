with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\security\consent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the log_consent call - needs role parameter
old = '''            # Audit log
            self.audit.log_consent(user_id, record)'''

new = '''            # Audit log
            self.audit.log_consent(user_id, "asha", record)'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\security\consent.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed log_consent call')
else:
    print('Pattern not found')