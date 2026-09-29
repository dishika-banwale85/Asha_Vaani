with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the function and add the dependency
idx = content.find('@app.post("/api/profile/update")')
if idx >= 0:
    # Find the function signature end
    sig_end = content.find('):\n', idx)
    if sig_end >= 0:
        # Check if already has the dependency
        sig_text = content[idx:sig_end+2]
        if 'require_own_worker_or_role' not in sig_text:
            content = content[:sig_end] + ', user: dict = Depends(require_own_worker_or_role())' + content[sig_end:]
            print('SUCCESS: Added dependency to POST /api/profile/update')
        else:
            print('Already has dependency')
    else:
        print('Could not find signature end')
else:
    print('Could not find endpoint')

# Also need to add audit logging at the end of the function before return
# Find the return statement area
return_idx = content.find('return {\n        "status": "success",\n        "message": "Profile updated successfully"\n    }', idx)
if return_idx >= 0:
    # Check if audit log already there
    before_return = content[return_idx-500:return_idx]
    if 'audit_logger.log' not in before_return:
        audit_code = '''
    # Audit log
    audit_logger.log(
        AuditEventType.PROFILE_UPDATED,
        principal_id=user["username"],
        principal_role=user["role"],
        target_id=data.worker_id,
        target_type="profile",
        payload={"updated_fields": ["name", "state", "district", "village", "sub_center"]},
    )

'''
        content = content[:return_idx] + audit_code + content[return_idx:]
        print('SUCCESS: Added audit logging to POST /api/profile/update')
    else:
        print('Audit already present')

with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
    f.write(content)