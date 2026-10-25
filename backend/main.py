import os
import sys
import uvicorn

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from routers import chat, conversations
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

#Register Controllers / routers
app.include_router(chat.router)
app.include_router(conversations.router)

@app.get("/")
def home():
    return {"message": "Chatbot API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", 8000))

    print(f"[*] FastAPI server running at: http://{host}:{port}")
    print(f"[*] Interactive Swagger docs at: http://{host}:{port}/docs")

    module_target = "backend.main:app" if os.path.exists("backend") else "main:app"
    uvicorn.run(module_target, host=host, port=port, reload=True) 
