with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace
old = 'upgrade_users_table()\n\n\n\n\n# Models for incoming data'
new = '''upgrade_users_table()

# --- Initialize Security Modules ---
# Crypto
init_crypto(os.environ.get("MASTER_ENCRYPTION_KEY"))

# PII
pepper = os.environ.get("PII_PEPPER", "").encode() or None
init_pii(pepper=pepper, field_encryptor=get_field_encryptor())

# Audit
audit_hmac_key = os.environ.get("AUDIT_HMAC_KEY", "").encode() or None
audit_logger = init_audit("audit.db", hmac_key=audit_hmac_key)

# Consent Manager
consent_manager = ConsentManager(get_consent_encryptor(), audit_logger)

# --- Upgrade users table to add role and consent columns ---
def upgrade_users_table_security():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'asha'")
    except:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN consent_version INTEGER DEFAULT 0")
    except:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN consent_flags TEXT")
    except:
        pass
    conn.commit()
    conn.close()

upgrade_users_table_security()





# Models for incoming data'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Replacement done')
else:
    print('OLD STRING NOT FOUND')
    idx = content.find('upgrade_users_table()')
    if idx >= 0:
        print('Found at:', idx)
        print(repr(content[idx:idx+100]))