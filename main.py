from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import time
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Eye of Horus API",
    description="Ancient Egypt Expert System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# Models
class QuestionRequest(BaseModel):
    question: str
    language: Optional[str] = "en"

class AnswerResponse(BaseModel):
    answer: str
    processing_time: float
    source: Optional[str] = None
    status: str

# Initialize QA System
try:
    from agents.qa_agent import QAAgent
    print("Current working directory:", os.getcwd())
    pdf_path = os.path.join(os.path.dirname(__file__), "data", "ancient_egypt_data.pdf")
    print("Does data/ exist?", os.path.isdir("data"))
    print("Does data/ancient_egypt_data.pdf exist?", os.path.isfile("data/ancient_egypt_data.pdf"))
    if not os.path.exists(pdf_path):
        raise RuntimeError("PDF data file not found!")
    
    qa_system = QAAgent(pdf_path)
    print(" QA System initialized successfully!")
except Exception as e:
    print(f" Failed to initialize QA System: {e}")
    qa_system = None


@app.get("/welcome")
def display_welcome():
    welcome_message = {
        "title": " Eye of Horus - Ancient Egypt Expert System  ",
        "intro": "Welcome to our little project! ",
        "description": "I'm here to help you explore the wonders of Ancient Egypt.",
        "topics": "Ask me anything about pharaohs, temples, mummies, or lost secrets!",
        "commands": {
            "ask": " Type your question to begin.",
            "clear": " Type 'clear' to clear the screen.",
            "exit": " Type 'exit' to quit the program."
        }
    }
    return welcome_message
@app.post("/api/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about Ancient Egypt
    
    Parameters:
    - question: Your question (e.g. "Who was Ramses II?")
    - language: Preferred language (en/ar/fr/es/de/it/pt)
    """
    if qa_system is None:
        raise HTTPException(status_code=503, detail="Service unavailable - QA system not initialized")
    
    try:
        start_time = time.time()
        
        # Process question
        pdf_ans, web_ans1, _ = qa_system.get_answer(request.question)
        
        # Generate response
        if pdf_ans:
            response = {
                "answer": pdf_ans,
                "source": "local_database",
                "status": "success"
            }
        elif web_ans1 and "http" in web_ans1:
            website = web_ans1.split("http")[1].split("/")[2].replace("www.", "")
            response = {
                "answer": web_ans1.split("http")[0],
                "source": website,
                "status": "success"
            }
        elif web_ans1:
            response = {
                "answer": web_ans1,
                "source": "web",
                "status": "success"
            }
        else:
            response = {
                "answer": "Sorry, I don't have an answer for this question.",
                "source": None,
                "status": "no_results"
            }
        
        return {
            **response,
            "processing_time": time.time() - start_time
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Check API status"""
    return {
        "status": "ready" if qa_system else "degraded",
        "service": "Eye of Horus API",
        "version": "1.0.0"
    }

@app.get("/", include_in_schema=False)
async def welcome():
    """Simple welcome page"""
    return {
        "message": "Welcome to Eye of Horus API",
        "endpoints": {
            "ask_question": "POST /api/ask",
            "documentation": "/docs",
            "health_check": "GET /api/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)