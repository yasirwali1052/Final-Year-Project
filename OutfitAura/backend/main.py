from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from groq import Groq
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

# --- Configuration Setup ---
# load_dotenv(dotenv_path='.env')
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_KEY = "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"

# Validate environment variables
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found")

# --- Groq Client Initialization ---
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groq client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Groq client: {e}")
    raise

# --- LangChain Setup ---
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    max_token_limit=2000,
    input_key="input",
    output_key="output"
)

# Prompt template
fashion_prompt = PromptTemplate(
    input_variables=["chat_history", "user_input"],
    template="""\
As OutfitAura's Fashion AI Expert, provide detailed advice considering:
- Current trends and timeless combinations
- Body type and skin tone analysis
- Color theory and seasonal appropriateness
- User's mentioned preferences

Chat History:
{chat_history}

User Query: {user_input}
FashionBot Response:
"""
)

# --- Core Processing Chain ---
def groq_processor(prompt_text: str) -> str:
    try:
        print(f"📝 Processing prompt: {prompt_text[:100]}...")
        print(f"🔑 Using model: llama-3.3-70b-versatile")
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_text}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=500
        )
        if not response.choices:
            print("❌ Empty response received from Groq API")
            raise ValueError("Empty response from Groq API")
        print(f"✅ Successfully got response from Groq API. Length: {len(response.choices[0].message.content)} chars")
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️ Groq API Error: {error_msg}")
        print(f"⚠️ Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"⚠️ Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"⚠️ Response body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
        return f"I apologize, but I'm having trouble accessing the fashion database. Technical details: {error_msg}"

# ✅ Fixed fashion_chain
fashion_chain = (
    RunnablePassthrough.assign(
        chat_history=lambda _: memory.load_memory_variables({}).get("chat_history", []),
        user_input=lambda x: x["user_input"]
    )
    | fashion_prompt
    | RunnableLambda(lambda x: groq_processor(x.text))
    | StrOutputParser()
)

# --- FastAPI Setup ---
app = FastAPI(title="OutfitAura Fashion Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def health_check():
    return {"status": "active", "service": "OutfitAura Fashion API"}

@app.post("/chat")
async def chat_handler(request: ChatRequest):
    try:
        print(f"📨 Received message: {request.message}")
        user_input = request.message.strip()

        if not user_input:
            raise HTTPException(status_code=400, detail="Empty message received")

        print("🔄 Processing request...")
        bot_response = fashion_chain.invoke({"user_input": user_input})
        print(f"📤 Sending response: {bot_response[:100]}...")

        memory.save_context(
            {"input": user_input},
            {"output": bot_response}
        )

        return {"response": bot_response}

    except HTTPException as he:
        print(f"🚫 HTTP Error: {str(he)}")
        raise he
    except Exception as e:
        print(f"🚨 API Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
