import os
import shutil
import uuid
import requests
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from dotenv import load_dotenv
from groq import Groq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from parsing_service import parsing_service
from tryon_service import tryon_service

# --- Configuration Setup ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
COLAB_TRYON_URL = os.getenv("COLAB_TRYON_URL", None)

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

# --- Simple Memory Implementation (Replacement for ConversationBufferMemory) ---
class SimpleConversationMemory:
    def __init__(self, max_messages=10):
        self.messages = []
        self.max_messages = max_messages
    
    def save_context(self, inputs: dict, outputs: dict):
        """Save conversation context"""
        user_message = inputs.get("input", "")
        bot_message = outputs.get("output", "")
        
        self.messages.append({"role": "user", "content": user_message})
        self.messages.append({"role": "assistant", "content": bot_message})
        
        # Keep only the last max_messages pairs
        if len(self.messages) > self.max_messages * 2:
            self.messages = self.messages[-(self.max_messages * 2):]
    
    def load_memory_variables(self, inputs: dict = None):
        """Load memory variables for the chain"""
        # Format conversation history as a string
        history_text = ""
        for msg in self.messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
        
        return {"chat_history": history_text if history_text else "No previous conversation."}
    
    def clear(self):
        """Clear conversation history"""
        self.messages = []

# Initialize memory
memory = SimpleConversationMemory(max_messages=10)

# Enhanced Prompt template with better formatting instructions
fashion_prompt = PromptTemplate(
    input_variables=["chat_history", "user_input"],
    template="""
You are OutfitAura's Fashion AI Expert. Your job is to give clean, practical, and stylish fashion advice. 
Always follow the rules below exactly.

============================
FORMATTING RULES (STRICT)
============================
1. Use numbered lists (1., 2., 3.) when giving multiple suggestions.
2. Do NOT use asterisks (*), dashes (-), bullets, markdown formatting, emojis, hashtags, or symbols.
3. Keep answers clean, simple, and easy to read.
4. Use short paragraphs of 1–3 lines.
5. Do not use long descriptive paragraphs.
6. No code blocks unless the user asks.

============================
CONTENT RULES
============================
1. Always give practical, real-world outfit advice.
2. Consider weather, season, occasion, style preference, and comfort.
3. For medical scenarios (MRI, X-ray), recommend metal-free and comfortable clothing.
4. For weddings or events, consider formality, venue, colors, and trends.
5. If the user asks for non-fashion topics, politely redirect back to fashion.

============================
LENGTH RULES
============================
1. Normal answers: 4–8 lines.
2. Outfits or lists: 3–6 points maximum.
3. If the user asks for very detailed help, expand but keep clarity.

============================
CONTEXT RULES
============================
Use chat history to stay consistent. Adapt advice based on:
- Body type (if given)
- Skin tone (if given)
- User style preferences
- Climate or location
- Occasion or event type

============================
Chat History:
{chat_history}

User Query:
{user_input}

Provide your best fashion advice now.
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
            temperature=0.7,  # Balanced creativity and consistency
            max_tokens=1024    # Increased for complete detailed responses
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
    """Clean up response formatting without truncating"""
    response = response.strip()
    
    # Remove unnecessary verbose phrases but keep the content
    remove_phrases = [
        "I'd be delighted to help you with that",
        "Please feel free to ask",
        "I'm here to assist you"
    ]
    for phrase in remove_phrases:
        response = response.replace(phrase, "")
    
    # Clean up extra whitespace
    response = ' '.join(response.split())
    
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
        chat_history=lambda _: memory.load_memory_variables({}).get("chat_history", "No previous conversation."),
        user_input=lambda x: x["user_input"],
        query_type=lambda x: classify_query(x["user_input"])
    )
    | fashion_prompt
    | RunnableLambda(lambda x: groq_processor(x.text))
    | StrOutputParser()
)

# --- FastAPI Setup ---
app = FastAPI(title="OutfitAura Fashion Assistant API", version="2.0")
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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


@app.post("/api/parse-human")
async def parse_human(
    request: Request,
    person_image: UploadFile = File(...),
):
    if not person_image or person_image.filename == "":
        raise HTTPException(status_code=400, detail="Person image is required")

    if person_image.content_type and not person_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    temp_filename = f"{uuid.uuid4().hex}_{person_image.filename}"
    temp_path = UPLOAD_DIR / temp_filename

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(person_image.file, buffer)

        parsing_path = parsing_service.generate_parsing(temp_path)
        relative_path = parsing_path.relative_to(STATIC_DIR)
        base_url = str(request.base_url).rstrip("/")
        public_url = f"{base_url}/static/{relative_path.as_posix()}"

        return {"parsing_image_url": public_url}
    except Exception as exc:
        print(f"🚨 Parsing error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to generate parsing result")
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/generate-tryon")
async def generate_tryon(
    request: Request,
    person_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
):
    if not person_image or person_image.filename == "":
        raise HTTPException(status_code=400, detail="Person image is required")
    if not garment_image or garment_image.filename == "":
        raise HTTPException(status_code=400, detail="Garment image is required")

    for upload in (person_image, garment_image):
        if upload.content_type and not upload.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image uploads are supported")

    temp_person = UPLOAD_DIR / f"{uuid.uuid4().hex}_{person_image.filename}"
    temp_garment = UPLOAD_DIR / f"{uuid.uuid4().hex}_{garment_image.filename}"

    try:
        # Save uploaded images locally
        with temp_person.open("wb") as buffer:
            shutil.copyfileobj(person_image.file, buffer)
        with temp_garment.open("wb") as buffer:
            shutil.copyfileobj(garment_image.file, buffer)

        # Generate parsing locally (fast)
        print("🔄 Generating parsing mask...")
        parsing_path = parsing_service.generate_parsing(temp_person)
        print("✅ Parsing complete")

        # Check if Colab URL is configured
        if COLAB_TRYON_URL:
            # Forward to Colab for GPU inference
            print(f"🚀 Sending to Colab: {COLAB_TRYON_URL}")
            
            with open(temp_person, "rb") as p, \
                 open(temp_garment, "rb") as g, \
                 open(parsing_path, "rb") as parse:
                
                files = {
                    "person_image": (person_image.filename, p, person_image.content_type or "image/jpeg"),
                    "garment_image": (garment_image.filename, g, garment_image.content_type or "image/jpeg"),
                    "parsing_image": ("parsing.png", parse, "image/png")
                }
                
                try:
                    response = requests.post(
                        COLAB_TRYON_URL,
                        files=files,
                        timeout=300  # 5 minutes timeout
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get("status") == "success":
                        # Return base64 image to frontend
                        return {"tryon_image_base64": data["tryon_image_base64"]}
                    else:
                        error_msg = data.get("error", "Unknown error from Colab")
                        print(f"🚨 Colab error: {error_msg}")
                        raise HTTPException(status_code=500, detail=f"Colab inference failed: {error_msg}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"🚨 Request to Colab failed: {e}")
                    raise HTTPException(
                        status_code=503,
                        detail=f"Failed to connect to Colab service. Make sure Colab is running and URL is correct."
                    )
        else:
            # Fallback to local try-on service (CPU, slow)
            print("⚠️ COLAB_TRYON_URL not set, using local CPU inference (slow)...")
            tryon_path = tryon_service.generate_tryon(temp_person, temp_garment, parsing_path)
            
            relative_path = tryon_path.relative_to(STATIC_DIR)
            base_url = str(request.base_url).rstrip("/")
            public_url = f"{base_url}/static/{relative_path.as_posix()}"
            
            return {"tryon_image_url": public_url}
            
    except HTTPException:
        raise
    except Exception as exc:
        print(f"🚨 Try-on error: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate virtual try-on result: {str(exc)}")
    finally:
        # Clean up temp files
        for temp_file in (temp_person, temp_garment):
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting OutfitAura Fashion Assistant API v2.0")
    uvicorn.run(app, host="0.0.0.0", port=8001)