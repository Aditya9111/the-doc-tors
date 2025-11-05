from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router
from .config import OPENAI_API_KEY

app = FastAPI(
    title="RAG Zip Project", 
    version="1.0",
    description="A RAG (Retrieval-Augmented Generation) API for processing ZIP files containing documents and code",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": "Welcome to the RAG Zip API",
        "version": "1.0",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "ingest": "/api/ingest",
            "ingest_zip": "/api/ingest_zip",
            "ingest_versioned": "/api/ingest_versioned",
            "query": "/api/query",
            "generate_documentation": "/api/generate_documentation",
            "versions": "/api/versions",
            "stats": "/api/stats"
        }
    }

@app.get("/info")
def info():
    """Get API information and configuration status"""
    return {
        "api_name": "RAG Zip Project",
        "version": "1.0",
        "openai_configured": bool(OPENAI_API_KEY),
        "features": [
            "ZIP file ingestion",
            "Advanced document chunking",
            "Vector similarity search",
            "Question answering with context",
            "Support for multiple file types",
            "Automatic documentation generation",
            "Version management system"
        ]
    }
