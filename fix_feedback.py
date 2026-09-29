with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the corrupted feedback endpoint
old = '''        )edbackInput):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE chat_logs SET feedback = ? WHERE id = ?",
            (feedback_data.feedback, feedback_data.log_id)
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Consent Endpoints ---'''

new = '''        )

    return {"response": bot_reply, "log_id": log_id}

except Exception as e:
    return {"response": f"Backend processing error: {str(e)}", "log_id": None}


@app.post("/feedback")
async def log_feedback(feedback_data: FeedbackInput):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE chat_logs SET feedback = ? WHERE id = ?",
            (feedback_data.feedback, feedback_data.log_id)
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- Consent Endpoints ---'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed feedback endpoint')
else:
    print('Pattern not found - trying alternative')
    # Try to find the corrupted part
    idx = content.find(')edbackInput')
    if idx >= 0:
        print('Found corruption at:', idx)
        print(repr(content[idx-100:idx+200]))