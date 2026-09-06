import os
import sqlite3
import hashlib
from fastapi import HTTPException
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


from dotenv import load_dotenv  # <-- 1. Import the library

load_dotenv()

# 1. Initialize the app ONCE with your title
app = FastAPI(title="NVBDCP RAG Decision Support Backend")

# --- AUTHENTICATION SYSTEM ---

# 1. Pydantic Model for incoming login/signup data
class UserAuth(BaseModel):
    username: str
    password: str

# 2. Secure Password Hashing
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# 3. Initialize the SQLite Users Database
def init_user_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password_hash TEXT)''')
    conn.commit()
    conn.close()

init_user_db()

# 4. Signup Endpoint
@app.post("/signup")
def signup(user: UserAuth):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        # Save the username and the SECURE HASH of the password
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                  (user.username, hash_password(user.password)))
        conn.commit()
        # Return a simple token so the phone knows they are logged in
        return {"message": "Account created!", "token": f"asha_{user.username}_valid"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists. Please login.")
    finally:
        conn.close()

# 5. Login Endpoint
@app.post("/login")
def login(user: UserAuth):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username=?", (user.username,))
    result = c.fetchone()
    conn.close()

    # Check if user exists AND password matches the hash
    if result and result[0] == hash_password(user.password):
        return {"message": "Login successful", "token": f"asha_{user.username}_valid"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

# 2. Attach the CORS Middleware to it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any frontend to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# --- SQLite Database Initialization ---
DB_NAME = "feedback.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_message TEXT,
            bot_response TEXT,
            feedback INTEGER DEFAULT 0  -- 1 for thumbs up, -1 for thumbs down
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Data Models ---
class ChatInput(BaseModel):
    message: str
    history: list = []

class FeedbackInput(BaseModel):
    log_id: int
    feedback: int  # 1 for thumbs up, -1 for thumbs down

# --- RAG Setup ---
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)
# Change k=3 to k=6 so it doesn't miss your text file!
retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
primary_llm = ChatGroq(model_name="openai/gpt-oss-20b", temperature=0.3)
backup_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
robust_llm = primary_llm.with_fallbacks([backup_llm])
   #-------------used for offline Puspose-----------------

#local_llm = ChatOllama(model="gemma2:2b", temperature=0.3)
def build_retrieval_query(user_msg: str, history: list) -> str:
    if len(user_msg.strip().split()) <= 4 and history:
        last_bot_msg = next((m["text"] for m in reversed(history) if m["sender"] == "bot"), "")
        return f"{last_bot_msg} {user_msg}"
    return user_msg

@app.post("/chat")
async def chat_with_rag(chat_input: ChatInput):
    user_msg = chat_input.message

    try:
        retrieval_query = build_retrieval_query(user_msg, chat_input.history)
        docs = retriever.invoke(retrieval_query)
        retrieved_context = "\n\n---\n\n".join([doc.page_content for doc in docs])

        
        system_prompt = f"""
You are "Asha Mitra", an expert clinical and administrative assistant for ASHA workers in Madhya Pradesh. 

CRITICAL ROUTING INSTRUCTIONS: You must classify the user's question into one of five categories and respond accordingly:

--- BUCKET 1: Official Protocols, Guidelines, and Incentives ---
If the user asks about NVBDCP rules, drug dosages, ASHA incentives, reporting hierarchies, or state protocols:
- You MUST answer strictly using ONLY the "OFFICIAL NVBDCP GUIDELINE CONTEXT" below. 
- If the exact amount or rule is not in the context, say: "Mera database abhi is official guideline ke baare mein update nahi hai."

--- BUCKET 2: General Medical & Biological Knowledge ---
If the user asks about general science, biology, or disease mechanics (including Dengue, Cancer, etc.):
- You may use your internal medical training to provide a clear, accurate, and educational answer. 

--- BUCKET 3: Live Data & Current Affairs ---
If the user asks for real-time data or live statistics:
- You MUST politely decline. Say: "I am currently an offline assistant and do not have access to live internet data."

--- BUCKET 4: Greetings & Casual Chit-Chat ---
If the user greets you, asks how you are, makes casual conversation, or asks clarifying questions (e.g., "kya samjhe?", "what do you mean?"):
- Respond naturally and conversationally based on the chat history. 
- Be polite, helpful, and human-like. You are allowed to explain yourself if the user asks what you meant.

--- BUCKET 5: Hard Endings & True Gibberish ---
ONLY if the user explicitly ends the conversation (e.g., "bye", "no thanks") OR types pure keyboard mashing (e.g., "asdfgh"):
- Generate a natural, very brief goodbye (e.g., "Theek hai, dhanyawad!", "Take care!").
- Keep it under 5 words and DO NOT ask any follow-up questions.

GENERAL RULES:
1. EXTREME BREVITY: Provide very short, bulleted answers (2-3 sentences max) for medical/administrative questions.
2. TRANSLATION COMMANDS: If the user explicitly asks you to "explain in Hindi" or "translate", just translate the facts using your internal knowledge. 
3. LANGUAGE CHAMELEON: Reply in the exact same language the user typed (English or Hindi/Hinglish). Do not switch language on your own; only switch if the user's latest message is clearly in a different language than before.
4. CONDITIONAL FOLLOW-UP (STRICT): Suggest 1 follow-up question ONLY IF:
   a) You successfully answered a BUCKET 1 or BUCKET 2 question, AND
   b) The follow-up topic is explicitly visible as a heading, bullet, or sub-topic inside the OFFICIAL NVBDCP GUIDELINE CONTEXT below.
   Do NOT invent a "logical next step" follow-up that sounds reasonable but isn't literally present in the context.
   If no such follow-up topic exists in the context, end your response with no follow-up at all — do not force one.

OFFICIAL NVBDCP GUIDELINE CONTEXT:
{retrieved_context}
"""
        # 1. Start with the System Prompt
        messages = [SystemMessage(content=system_prompt)]
        
        # 2. Add the past conversational history
        for past_msg in chat_input.history:
            if past_msg["sender"] == "user":
                messages.append(HumanMessage(content=past_msg["text"]))
            elif past_msg["sender"] == "bot":
                messages.append(AIMessage(content=past_msg["text"]))
                
        # 3. Add the brand new message at the end
        messages.append(HumanMessage(content=user_msg))

        # Now send the whole package to Groq
        response = robust_llm.invoke(messages)


        # --------Change from robust_llm to local_llm:---------

        #response = local_llm.invoke(messages)

        bot_reply = response.content

        # Save conversation to SQLite
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO chat_logs (timestamp, user_message, bot_response) VALUES (?, ?, ?)",
            (now, user_msg, bot_reply)
        )
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()

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