with open(r'C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the chat function and fix its try/except structure
# The function starts at "async def chat_with_rag"
func_start = content.find('async def chat_with_rag(chat_input: ChatInput, user: dict = Depends(get_current_user)):')
if func_start < 0:
    print('Function not found')
    exit()

# Find the end of the function - look for the next @app. or async def at module level
# But first, let's find the current broken structure
# The try: is at around position 896 from function start
# The except is at module level (position 46563)

# Let's find the return statement that should be inside the try
# and the except that should be inside the function

# Search for the pattern: the function has:
# 1. consent check code
# 2. audit log request
# 3. try: (original RAG logic)
# 4. ... RAG logic ...
# 5. storage code
# 6. audit log response
# 7. return statement
# 8. MISSING except inside function
# 9. except at module level (wrong)

# We need to:
# 1. Move try: to wrap everything from after audit log request to the return
# 2. Add proper except inside function (4-space indent)

# Let's find the key positions
idx = func_start

# Find "try:" inside function (first one after function start)
try_idx = content.find('\n    try:', func_start)
print(f'try: at {try_idx}')

# Find the return statement inside the try block
return_idx = content.find('\n        return {"response": bot_reply, "log_id": log_id}', try_idx)
print(f'return at {return_idx}')

# Find the module-level except (0 indent)
module_except_idx = content.find('\nexcept Exception as e:')
print(f'module except at {module_except_idx}')

# The function should end before the module-level except
# Find the next @app. or async def after the return
next_endpoint = content.find('\n\n@app.', return_idx)
if next_endpoint < 0:
    next_endpoint = content.find('\n\nasync def ', return_idx)
if next_endpoint < 0:
    next_endpoint = content.find('\n\n# ---', return_idx)
print(f'next endpoint at {next_endpoint}')

# Now reconstruct the function body properly
# From func_start to next_endpoint is the function
func_body = content[func_start:next_endpoint]
print(f'Function body length: {len(func_body)}')
print('--- Function body (first 500 chars) ---')
print(func_body[:500])
print('--- Function body (last 500 chars) ---')
print(func_body[-500:])