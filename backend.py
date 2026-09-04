import os
import sqlite3
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

@app.post("/chat")
async def chat_with_rag(chat_input: ChatInput):
    user_msg = chat_input.message

    try:
        docs = retriever.invoke(user_msg)
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
3. LANGUAGE CHAMELEON: Reply in the exact same language the user typed (English or Hindi/Hinglish).
4. CONDITIONAL FOLLOW-UP: Suggest 1 relevant follow-up question ONLY IF you successfully answered a BUCKET 1 or BUCKET 2 question.

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