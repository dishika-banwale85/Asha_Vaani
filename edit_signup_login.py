with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update signup endpoint - add role and audit
old_signup = '''# 4. Signup Endpoint
@app.post("/signup")
def signup(user: UserAuth):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        # Save the username and the SECURE HASH of the password
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                  (user.username, hash_password(user.password)))
        conn.commit()
        
        # FIX: Generate a real JWT for the newly signed-up user!
        access_token = create_access_token(user.username)
        
        return {"message": "Account created!", "token": access_token}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists. Please login.")
    finally:
        conn.close()'''

new_signup = '''# 4. Signup Endpoint
@app.post("/signup")
def signup(user: UserAuth):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        # Save the username and the SECURE HASH of the password
        # New users default to role="asha"
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                  (user.username, hash_password(user.password), "asha"))
        conn.commit()
        
        # FIX: Generate a real JWT for the newly signed-up user!
        access_token = create_access_token(user.username, "asha")
        
        # Audit log
        audit_logger.log(
            AuditEventType.SIGNUP,
            principal_id=user.username,
            principal_role="asha",
            payload={"action": "signup", "method": "password"},
        )
        
        return {"message": "Account created!", "token": access_token}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists. Please login.")
    finally:
        conn.close()'''

# Update login endpoint - add role from DB and audit
old_login = '''# 5. Login Endpoint
@app.post("/login")
def login(user: UserAuth):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "SELECT password_hash FROM users WHERE username=?",
        (user.username,)
    )
    result = c.fetchone()
    conn.close()

    if result:
        stored_hash = result[0]

        # Check if password is already using bcrypt
        if (
            stored_hash.startswith("$2b$")
            or stored_hash.startswith("$2a$")
            or stored_hash.startswith("$2y$")
        ):
            password_valid = bcrypt.checkpw(
                user.password.encode("utf-8"),
                stored_hash.encode("utf-8")
            )

        # Existing users: verify old SHA-256 hash
        else:
            old_hash = hashlib.sha256(
                user.password.encode("utf-8")
            ).hexdigest()

            password_valid = (stored_hash == old_hash)

            # Upgrade old SHA-256 hash to bcrypt
            if password_valid:
                new_hash = bcrypt.hashpw(
                    user.password.encode("utf-8"),
                    bcrypt.gensalt()
                ).decode("utf-8")

                conn = sqlite3.connect("users.db")
                c = conn.cursor()

                c.execute(
                    "UPDATE users SET password_hash=? WHERE username=?",
                    (new_hash, user.username)
                )

                conn.commit()
                conn.close()

    else:
        password_valid = False

    if password_valid:
        access_token = create_access_token(user.username)

        return {
            "message": "Login successful",
            "token": access_token
        }
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )'''

new_login = '''# 5. Login Endpoint
@app.post("/login")
def login(user: UserAuth):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    # Get password_hash AND role
    c.execute(
        "SELECT password_hash, role FROM users WHERE username=?",
        (user.username,)
    )
    result = c.fetchone()
    conn.close()

    if result:
        stored_hash = result[0]
        user_role = result[1] if result[1] else "asha"

        # Check if password is already using bcrypt
        if (
            stored_hash.startswith("$2b$")
            or stored_hash.startswith("$2a$")
            or stored_hash.startswith("$2y$")
        ):
            password_valid = bcrypt.checkpw(
                user.password.encode("utf-8"),
                stored_hash.encode("utf-8")
            )

        # Existing users: verify old SHA-256 hash
        else:
            old_hash = hashlib.sha256(
                user.password.encode("utf-8")
            ).hexdigest()

            password_valid = (stored_hash == old_hash)

            # Upgrade old SHA-256 hash to bcrypt
            if password_valid:
                new_hash = bcrypt.hashpw(
                    user.password.encode("utf-8"),
                    bcrypt.gensalt()
                ).decode("utf-8")

                conn = sqlite3.connect("users.db")
                c = conn.cursor()

                c.execute(
                    "UPDATE users SET password_hash=? WHERE username=?",
                    (new_hash, user.username)
                )

                conn.commit()
                conn.close()

    else:
        password_valid = False

    if password_valid:
        access_token = create_access_token(user.username, user_role)
        
        # Audit log
        audit_logger.log(
            AuditEventType.LOGIN,
            principal_id=user.username,
            principal_role=user_role,
            payload={"action": "login", "method": "password", "success": True},
        )

        return {
            "message": "Login successful",
            "token": access_token
        }
    else:
        # Audit failed login
        audit_logger.log(
            AuditEventType.LOGIN,
            principal_id=user.username,
            principal_role="unknown",
            payload={"action": "login", "method": "password", "success": False},
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )'''

if old_signup in content:
    content = content.replace(old_signup, new_signup)
    print('SUCCESS: Signup updated')
else:
    print('Signup NOT FOUND')

if old_login in content:
    content = content.replace(old_login, new_login)
    print('SUCCESS: Login updated')
else:
    print('Login NOT FOUND')

with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
    f.write(content)