with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update /chat endpoint signature to add user dependency
idx = content.find('@app.post("/chat")')
if idx >= 0:
    sig_end = content.find('chat_input: ChatInput):', idx)
    if sig_end >= 0:
        sig_text = content[idx:sig_end+20]
        if 'user: dict = Depends(get_current_user)' not in sig_text:
            content = content[:sig_end+20] + ', user: dict = Depends(get_current_user)' + content[sig_end+20:]
            print('SUCCESS: Added user dependency to /chat')
        else:
            print('User dependency already present')

# Now update the function body - add consent check at the start
try_idx = content.find('try:\n        # Ensure you have', idx)
if try_idx >= 0:
    consent_code = '''    # Consent check
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT consent_version FROM users WHERE username=?", (user["username"],))
    row = c.fetchone()
    conn.close()
    
    consent_version = row[0] if row and row[0] else 0
    if consent_version < CURRENT_CONSENT_VERSION:
        return {
            "consent_required": True,
            "message": "Please accept the updated consent form before using chat.",
            "consent_form_version": CURRENT_CONSENT_VERSION,
            "consent_categories": [
                {"id": cat["id"], "title": cat["title"], "description": cat["description"], "required": cat["required"]}
                for cat in CONSENT_FORM_CONTENT["categories"]
            ]
        }
    
    # Audit: log chat request (sanitized)
    audit_logger.log(
        AuditEventType.CHAT_QUERY,
        principal_id=user["username"],
        principal_role=user["role"],
        payload={"query_hash": hashlib.sha256(chat_input.message.encode()).hexdigest()[:16]},
    )

    try:'''
    
    if 'consent_version < CURRENT_CONSENT_VERSION' not in content[try_idx:try_idx+200]:
        content = content[:try_idx] + consent_code + content[try_idx:]
        print('SUCCESS: Added consent check and audit to /chat')
    else:
        print('Consent check already present')

# Update the storage part to encrypt user message and add audit for response
store_idx = content.find('conn = sqlite3.connect(DB_NAME)\n        cursor = conn.cursor()\n        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")\n        cursor.execute(\n            "INSERT INTO chat_logs (timestamp, user_message, bot_response) VALUES (?, ?, ?)",\n            (now, user_msg, bot_reply)\n        )')
if store_idx >= 0:
    new_storage = '''        # Encrypt user message for storage
        field_encryptor = get_field_encryptor()
        encrypted_user_msg = field_encryptor.encrypt(user_msg, f"chat:{user['username']}")
        
        # Save conversation to SQLite with encrypted user_message
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO chat_logs (timestamp, user_message, bot_response) VALUES (?, ?, ?)",
            (now, encrypted_user_msg, bot_reply)
        )
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        
        # Audit: log chat response
        audit_logger.log(
            AuditEventType.CHAT_RESPONSE,
            principal_id=user["username"],
            principal_role=user["role"],
            payload={"response_hash": hashlib.sha256(bot_reply.encode()).hexdigest()[:16], "log_id": log_id},
        )'''
        
    if 'encrypted_user_msg' not in content[store_idx:store_idx+500]:
        content = content[:store_idx] + new_storage + content[store_idx+600:]
        print('SUCCESS: Updated storage with encryption and audit')
    else:
        print('Storage already updated')

with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
    f.write(content)