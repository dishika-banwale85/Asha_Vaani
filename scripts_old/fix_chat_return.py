with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The issue: 
# 1. The return statement is at 4-space indent but OUTSIDE the try block
# 2. The except is at module level (0 indent) - doesn't match the try
# 3. The function never properly ends before the next endpoint

# Fix: 
# - Move return inside try (8-space indent)
# - Add except block inside function (4-space indent) 
# - Remove the module-level except

# Find the exact patterns to fix
# Pattern 1: return outside try (4-space indent before it)
old_return = '''        )

    return {"response": bot_reply, "log_id": log_id}

except Exception as e:
    return {"response": f"Backend processing error: {str(e)}", "log_id": None}


@app.post("/feedback")'''

# Pattern 2: return inside try (8-space), with proper except inside function
new_return = '''        )

        return {"response": bot_reply, "log_id": log_id}

    except Exception as e:
        return {"response": f"Backend processing error: {str(e)}", "log_id": None}


@app.post("/feedback")'''

if old_return in content:
    content = content.replace(old_return, new_return)
    with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Fixed try/except structure in chat function')
else:
    print('Pattern not found')
    # Debug - find what's actually there
    idx = content.find('return {"response": bot_reply, "log_id": log_id}')
    if idx >= 0:
        print('Found return at:', idx)
        print(repr(content[idx-100:idx+200]))