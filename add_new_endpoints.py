with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('return {"status": "success"}\n    except Exception as e:\n        return {"status": "error", "message": str(e)}\n\n\n\nclass ProfileUpdateRequest')
if idx >= 0:
    new_endpoints = '''\n\n\n# --- Consent Endpoints ---
class ConsentInput(BaseModel):
    patient_data: bool
    audio_recording: bool
    analytics: bool
    location_tracking: bool
    referral_sharing: bool


@app.get("/api/consent")
def get_consent(user: dict = Depends(get_current_user)):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT consent_version FROM users WHERE username=?", (user["username"],))
    row = c.fetchone()
    conn.close()
    
    version = row[0] if row and row[0] else 0
    return {
        "version": version,
        "current_version": CURRENT_CONSENT_VERSION,
        "needs_update": version < CURRENT_CONSENT_VERSION,
        "categories": CONSENT_FORM_CONTENT["categories"]
    }


@app.post("/api/consent")
def update_consent(data: ConsentInput, user: dict = Depends(get_current_user)):
    flags = ConsentFlags(
        patient_data=data.patient_data,
        audio_recording=data.audio_recording,
        analytics=data.analytics,
        location_tracking=data.location_tracking,
        referral_sharing=data.referral_sharing,
        version=CURRENT_CONSENT_VERSION
    )
    
    valid, missing = consent_manager.validate_consent(flags)
    if not valid:
        raise HTTPException(status_code=400, detail=f"Required consents missing: {missing}")
    
    # Store encrypted consent flags
    consent_encryptor = get_consent_encryptor()
    encrypted = consent_encryptor.encrypt(flags.to_dict())
    
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "UPDATE users SET consent_version=?, consent_flags=? WHERE username=?",
        (CURRENT_CONSENT_VERSION, encrypted, user["username"])
    )
    conn.commit()
    conn.close()
    
    # Audit
    for cat in ConsentCategory:
        granted = flags.get_category(cat)
        if granted:
            consent_manager.record_consent(user["username"], flags)
    
    return {"status": "success", "message": "Consent updated"}


# --- Admin Endpoints ---
class RoleChangeRequest(BaseModel):
    username: str
    role: str  # "asha", "supervisor", "admin"


@app.post("/api/admin/change-role")
def change_role(data: RoleChangeRequest, user: dict = Depends(require_role("admin"))):
    if data.role not in ["asha", "supervisor", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET role=? WHERE username=?", (data.role, data.username))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    conn.commit()
    conn.close()
    
    audit_logger.log(
        AuditEventType.USER_ROLE_CHANGED,
        principal_id=user["username"],
        principal_role=user["role"],
        target_id=data.username,
        target_type="user",
        payload={"action": "role_changed", "new_role": data.role},
    )
    
    return {"status": "success", "message": f"Role updated to {data.role}"}


@app.get("/api/admin/audit/verify")
def verify_audit_chain(limit: int = 1000, user: dict = Depends(require_role("admin"))):
    valid, broken_id = audit_logger.verify_chain(limit)
    return {"valid": valid, "broken_entry_id": broken_id}


@app.get("/api/admin/audit/query")
def query_audit_logs(
    principal_id: str = None,
    event_type: str = None,
    start: str = None,
    end: str = None,
    limit: int = 100,
    user: dict = Depends(require_role("admin"))
):
    from datetime import datetime
    entries = audit_logger.query(
        principal_id=principal_id,
        event_type=AuditEventType(event_type) if event_type else None,
        start=datetime.fromisoformat(start) if start else None,
        end=datetime.fromisoformat(end) if end else None,
        limit=limit
    )
    return {"entries": [e.__dict__ for e in entries]}


'''

    content = content[:idx] + new_endpoints + content[idx:]
    print('SUCCESS: Added consent and admin endpoints')
else:
    print('Could not find insertion point')

with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
    f.write(content)