with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the corrupted chat endpoint signature
old = '''@app.post("/chat")
async def chat_with_rag(chat_input: ChatInpu, user: dict = Depends(get_current_user)t):
    user_msg = chat_input.message

        # Consent check
    conn = sqlite3.connect("users.db")'''

new = '''@app.post("/chat")
async def chat_with_rag(chat_input: ChatInput, user: dict = Depends(get_current_user)):
    user_msg = chat_input.message

    # Consent check
    conn = sqlite3.connect("users.db")'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed chat endpoint signature')
else:
    print('Pattern not found')
    idx = content.find('async def chat_with_rag')
    if idx >= 0:
        print(repr(content[idx:idx+200]))