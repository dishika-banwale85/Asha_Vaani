with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

checks = [
    ('@app.get("/api/consent")', 'Consent GET'),
    ('@app.post("/api/consent")', 'Consent POST'),
    ('@app.post("/api/admin/change-role")', 'Admin change-role'),
    ('@app.get("/api/admin/audit/verify")', 'Admin audit verify'),
]

for pattern, name in checks:
    if pattern in content:
        print(f'{name}: FOUND')
    else:
        print(f'{name}: NOT FOUND')