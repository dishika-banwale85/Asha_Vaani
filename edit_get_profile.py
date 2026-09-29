with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update GET /api/profile/{worker_id}
old = '''@app.get("/api/profile/{worker_id}")
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

new = '''@app.get("/api/profile/{worker_id}")
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

if old in content:
    content = content.replace(old, new)
    print('SUCCESS: GET profile updated')
else:
    print('GET profile NOT FOUND')
    idx = content.find('@app.get("/api/profile/')
    if idx >= 0:
        print(repr(content[idx:idx+500]))

with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
    f.write(content)