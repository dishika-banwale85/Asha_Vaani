with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact position and do surgical replacement
idx = content.find('return jwt.encode')
if idx >= 0:
    # Find the end of the function (next double newline after the print statement)
    end_idx = content.find('\n\n\n# 1. Initialize the app', idx)
    if end_idx >= 0:
        # Replace from idx to end_idx
        new_code = '''    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm="HS256"
    )


# --- Auth Dependency ---
async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"username": payload["sub"], "role": payload.get("role", "asha")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_role(*allowed_roles: str):
    async def check(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            audit_logger.log(
                AuditEventType.USER_ROLE_CHANGED,
                principal_id=user["username"],
                principal_role=user["role"],
                payload={"action": "permission_denied", "required_roles": allowed_roles, "endpoint": "unknown"},
            )
            raise HTTPException(status_code=403, detail=f"Role required: {', '.join(allowed_roles)}")
        return user
    return check


def require_own_worker_or_role(allowed_roles: list = None):
    if allowed_roles is None:
        allowed_roles = ["supervisor", "admin"]
    async def check(worker_id: str, user: dict = Depends(get_current_user)):
        if user["username"] == worker_id:
            return user
        if user["role"] in allowed_roles:
            return user
        audit_logger.log(
            AuditEventType.USER_ROLE_CHANGED,
            principal_id=user["username"],
            principal_role=user["role"],
            payload={"action": "permission_denied", "target_worker": worker_id, "endpoint": "profile"},
        )
        raise HTTPException(status_code=403, detail="Access denied: not your profile and insufficient role")
    return check


  #Get the API key securely
GOVT_API_KEY = os.getenv("GOVT_API_KEY")

# Check if key is loaded properly (terminal me print karke dekhne ke liye)
print("Govt API Key Loaded:", "YES" if GOVT_API_KEY else "NO / ERROR")




# 1. Initialize the app'''
        content = content[:idx] + new_code + content[end_idx + len('\n\n\n# 1. Initialize the app'):]
        with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('SUCCESS: Auth dependencies added via surgical replacement')
    else:
        print('Could not find end marker')
else:
    print('Could not find start marker')