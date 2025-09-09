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

# Enhanced Prompt template with better formatting instructions
fashion_prompt = PromptTemplate(
    input_variables=["chat_history", "user_input"],
    template="""\
You are OutfitAura's Fashion AI Expert. Provide helpful, well-formatted responses following these guidelines:

RESPONSE FORMATTING RULES:
- For lists: Use clear numbering (1., 2., 3.) with brief, actionable points
- For single recommendations: Keep it concise and specific
- For general advice: Use bullet points or short paragraphs
- Always be friendly but professional
- Use simple, easy-to-understand language

CONTENT GUIDELINES:
- Focus on practical, actionable fashion advice
- Consider body types, skin tones, occasions, and current trends
- For medical situations (MRI, X-ray): Prioritize safety and comfort
- For special occasions: Balance style with appropriateness
- If asked about non-fashion topics: Politely redirect to fashion-related help

CONTEXT AWARENESS:
- MRI/Medical: Focus on metal-free, comfortable clothing
- Weddings: Consider formality, venue, season, and role
- Daily wear: Balance comfort, style, and practicality
- Special events: Match outfit to occasion and dress code

Chat History:
{chat_history}

User Query: {user_input}

Provide your fashion advice now:
"""
)

# --- Enhanced Processing Chain ---
def groq_processor(prompt_text: str) -> str:
    try:
        print(f"📝 Processing prompt: {prompt_text[:100]}...")
        print(f"🔑 Using model: llama-3.3-70b-versatile")
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_text}],
            model="llama-3.3-70b-versatile",
            temperature=0.6,  # Slightly lower for more consistent formatting
            max_tokens=600    # Increased for better detailed responses
        )
        if not response.choices:
            print("❌ Empty response received from Groq API")
            raise ValueError("Empty response from Groq API")
        
        response_content = response.choices[0].message.content
        print(f"✅ Successfully got response from Groq API. Length: {len(response_content)} chars")
        
        # Post-process response for better formatting
        formatted_response = format_response(response_content)
        return formatted_response
        
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️ Groq API Error: {error_msg}")
        print(f"⚠️ Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"⚠️ Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"⚠️ Response body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
        return "Sorry, I'm having technical issues. Please ask about fashion advice and I'll help!"

def format_response(response: str) -> str:
    """Force very short responses"""
    response = response.strip()
    
    # Cut off at first 30 words if too long
    words = response.split()
    if len(words) > 30:
        response = ' '.join(words[:30])
    
    # Remove unnecessary phrases
    remove_phrases = ["I'd be delighted", "Please feel free", "Here are some", "Let me help", "I recommend"]
    for phrase in remove_phrases:
        response = response.replace(phrase, "")
    
    return response.strip()

def classify_query(user_input: str) -> str:
    """Classify the type of query to provide context-aware responses"""
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ['mri', 'x-ray', 'scan', 'medical', 'hospital', 'doctor']):
        return 'medical'
    elif any(word in user_input_lower for word in ['wedding', 'marriage', 'bride', 'groom']):
        return 'wedding'
    elif any(word in user_input_lower for word in ['work', 'office', 'professional', 'business']):
        return 'professional'
    elif any(word in user_input_lower for word in ['party', 'club', 'night out', 'date']):
        return 'evening'
    elif any(word in user_input_lower for word in ['casual', 'everyday', 'daily', 'comfortable']):
        return 'casual'
    else:
        return 'general'

# Enhanced fashion chain with query classification
fashion_chain = (
    RunnablePassthrough.assign(
        chat_history=lambda _: memory.load_memory_variables({}).get("chat_history", []),
        user_input=lambda x: x["user_input"],
        query_type=lambda x: classify_query(x["user_input"])
    )
    | fashion_prompt
    | RunnableLambda(lambda x: groq_processor(x.text))
    | StrOutputParser()
)

# --- FastAPI Setup ---
app = FastAPI(title="OutfitAura Fashion Assistant API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def health_check():
    return {
        "status": "active", 
        "service": "OutfitAura Fashion API",
        "version": "2.0",
        "features": ["Fashion advice", "Outfit recommendations", "Style guidance"]
    }

@app.post("/chat")
async def chat_handler(request: ChatRequest):
    try:
        print(f"📨 Received message: {request.message}")
        user_input = request.message.strip()

        if not user_input:
            raise HTTPException(status_code=400, detail="Empty message received")

        # Check if it's a greeting or general inquiry
        if user_input.lower() in ['hi', 'hello', 'hey', 'how are you?', 'how are you']:
            return {
                "response": "Hello! I'm OutfitAura's Fashion AI, and I'm here to help you look and feel amazing! Whether you need outfit ideas, style advice, or fashion tips for any occasion, just ask me. What can I help you with today? 👗✨"
            }

        print("🔄 Processing request...")
        bot_response = fashion_chain.invoke({"user_input": user_input})
        print(f"📤 Sending response: {bot_response[:100]}...")

        # Save conversation context
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
            content={"error": "I'm experiencing some technical difficulties. Please try asking about fashion advice, and I'll do my best to help!"}
        )

@app.get("/health")
async def detailed_health():
    return {
        "api_status": "healthy",
        "groq_connection": "active",
        "memory_status": "operational",
        "supported_queries": [
            "Outfit recommendations",
            "Fashion advice",
            "Color matching",
            "Seasonal styling",
            "Occasion-specific outfits",
            "Body type guidance"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting OutfitAura Fashion Assistant API v2.0")
    uvicorn.run(app, host="0.0.0.0", port=8001)