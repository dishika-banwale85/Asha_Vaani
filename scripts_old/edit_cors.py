with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update first CORS middleware to use ALLOWED_ORIGINS env var
old_cors1 = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://0.0.0.0:8081",
        "http://127.0.0.1:8081",
        "http://localhost:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

new_cors1 = '''# CORS - use ALLOWED_ORIGINS env var
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8081,http://127.0.0.1:8081").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

# 2. Remove second CORS middleware (the duplicate with allow_origins=["*"])
old_cors2 = '''# 2. Attach the CORS Middleware to it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any frontend to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#add the routes that your frontend PWA will call to fetch or update this data'''

new_cors2 = '''#add the routes that your frontend PWA will call to fetch or update this data'''

if old_cors1 in content:
    content = content.replace(old_cors1, new_cors1)
    print('SUCCESS: First CORS updated')
else:
    print('First CORS NOT FOUND')

if old_cors2 in content:
    content = content.replace(old_cors2, new_cors2)
    print('SUCCESS: Second CORS removed')
else:
    print('Second CORS NOT FOUND')

with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
    f.write(content)