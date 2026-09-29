with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update GET /api/profile/{worker_id}
old_get_profile = '''#add the routes that your frontend PWA will call to fetch or update this data
@app.get("/api/profile/{worker_id}")
def get_profile(worker_id: str):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT name, state,district, village, sub_center FROM asha_profiles WHERE worker_id=?", (worker_id,))
    row = c.fetchone()
    
   
    if row:
        return {
            "worker_id": worker_id, 
            "name": row[0], 
            "state": row[1] if row[1] else "Madhya Pradesh",
            "district": row[2],
            "village": row[3], 
            "sub_center": row[4],
        }
    else:
        return {
            "worker_id": worker_id, 
            "name": worker_id.capitalize(),
            "state": "Madhya Pradesh",
            "village": "Not Assigned", 
            "sub_center": "Not Assigned",
        }'''

new_get_profile = '''#add the routes that your frontend PWA will call to fetch or update this data
@app.get("/api/profile/{worker_id}")
def get_profile(worker_id: str, user: dict = Depends(require_own_worker_or_role())):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT name, state,district, village, sub_center FROM asha_profiles WHERE worker_id=?", (worker_id,))
    row = c.fetchone()
    
   
    if row:
        return {
            "worker_id": worker_id, 
            "name": row[0], 
            "state": row[1] if row[1] else "Madhya Pradesh",
            "district": row[2],
            "village": row[3], 
            "sub_center": row[4],
        }
    else:
        return {
            "worker_id": worker_id, 
            "name": worker_id.capitalize(),
            "state": "Madhya Pradesh",
            "village": "Not Assigned", 
            "sub_center": "Not Assigned",
        }'''

# Update POST /api/profile/update
old_update_profile = '''@app.post("/api/profile/update")
def update_profile(data: ProfileUpdateRequest):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS asha_profiles
                 (worker_id TEXT PRIMARY KEY,
                  name TEXT,
                  village TEXT,
                  sub_center TEXT,
                  state TEXT,
                  district TEXT)''')

    # Add missing columns if they don't already exist
    try:
        c.execute("ALTER TABLE asha_profiles ADD COLUMN state TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE asha_profiles ADD COLUMN district TEXT")
    except sqlite3.OperationalError:
        pass

    # Check whether profile already exists
    c.execute(
        "SELECT worker_id FROM asha_profiles WHERE worker_id=?",
        (data.worker_id,)
    )
    exists = c.fetchone()

    if exists:
        c.execute("""
            UPDATE asha_profiles
            SET name=?,
                state=?,
                district=?,
                village=?,
                sub_center=?
            WHERE worker_id=?
        """, (
            data.name,
            data.state,
            data.district,
            data.village,
            data.sub_center,
            data.worker_id
        ))

    else:
        c.execute("""
            INSERT INTO asha_profiles
            (worker_id, name, state, district, village, sub_center)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.worker_id,
            data.name,
            data.state,
            data.district,
            data.village,
            data.sub_center
        ))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": "Profile updated successfully"
    }'''

new_update_profile = '''@app.post("/api/profile/update")
def update_profile(data: ProfileUpdateRequest, user: dict = Depends(require_own_worker_or_role())):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS asha_profiles
                 (worker_id TEXT PRIMARY KEY,
                  name TEXT,
                  village TEXT,
                  sub_center TEXT,
                  state TEXT,
                  district TEXT)''')

    # Add missing columns if they don't already exist
    try:
        c.execute("ALTER TABLE asha_profiles ADD COLUMN state TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE asha_profiles ADD COLUMN district TEXT")
    except sqlite3.OperationalError:
        pass

    # Check whether profile already exists
    c.execute(
        "SELECT worker_id FROM asha_profiles WHERE worker_id=?",
        (data.worker_id,)
    )
    exists = c.fetchone()

    if exists:
        c.execute("""
            UPDATE asha_profiles
            SET name=?,
                state=?,
                district=?,
                village=?,
                sub_center=?
            WHERE worker_id=?
        """, (
            data.name,
            data.state,
            data.district,
            data.village,
            data.sub_center,
            data.worker_id
        ))

    else:
        c.execute("""
            INSERT INTO asha_profiles
            (worker_id, name, state, district, village, sub_center)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.worker_id,
            data.name,
            data.state,
            data.district,
            data.village,
            data.sub_center
        ))

    conn.commit()
    conn.close()

    # Audit log
    audit_logger.log(
        AuditEventType.PROFILE_UPDATED,
        principal_id=user["username"],
        principal_role=user["role"],
        target_id=data.worker_id,
        target_type="profile",
        payload={"updated_fields": ["name", "state", "district", "village", "sub_center"]},
    )

    return {
        "status": "success",
        "message": "Profile updated successfully"
    }'''

if old_get_profile in content:
    content = content.replace(old_get_profile, new_get_profile)
    print('SUCCESS: GET profile updated')
else:
    print('GET profile NOT FOUND')

if old_update_profile in content:
    content = content.replace(old_update_profile, new_update_profile)
    print('SUCCESS: POST profile/update updated')
else:
    print('POST profile/update NOT FOUND')

with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
    f.write(content)