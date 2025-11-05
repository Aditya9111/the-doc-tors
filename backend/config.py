from pathlib import Path
import os
from dotenv import load_dotenv, find_dotenv

# Load .env from multiple common locations to be robust across working directories
# 1) Nearest .env relative to current working directory
load_dotenv(find_dotenv(usecwd=True))

# 2) Explicit project root .env (../.env from this file)
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
_PROJECT_ENV = _PROJECT_ROOT / ".env"
if _PROJECT_ENV.exists():
    load_dotenv(_PROJECT_ENV)

# 3) Backend-local .env (./.env next to this file)
_BACKEND_ENV = _HERE / ".env"
if _BACKEND_ENV.exists():
    load_dotenv(_BACKEND_ENV)

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DIR = BASE_DIR / "vectorstore"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
VECTOR_DIR.mkdir(exist_ok=True)

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# print(OPENAI_API_KEY)
# Do not raise at import time; downstream code should validate when needed.

# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# Documentation configuration
DOCUMENTATION_MODE = os.getenv("DOCUMENTATION_MODE", "standard")  # "standard" | "rag" | "hybrid"
RAG_DOCUMENTATION_CACHE = True  # Enable embedding caching for cost reduction
RAG_RETRIEVAL_K = 5  # Number of related documents to retrieve

# Efficient Documentation Generation Settings
DOC_MAX_FILE_SIZE = int(os.getenv("DOC_MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
DOC_MAX_TOKENS_PER_CHUNK = int(os.getenv("DOC_MAX_TOKENS_PER_CHUNK", 4000))
DOC_MAX_WORKERS = 3  # Fixed at 3 for simplicity
DOC_ENABLE_CACHING = os.getenv("DOC_ENABLE_CACHING", "true").lower() == "true"
DOC_CACHE_TTL_HOURS = int(os.getenv("DOC_CACHE_TTL_HOURS", 24))
DOC_MODE = os.getenv("DOC_MODE", "standard")  # fast/standard/deep

# OpenAI API configuration
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "60"))
OPENAI_LOG_REQUESTS = os.getenv("OPENAI_LOG_REQUESTS", "true").lower() == "true"
OPENAI_ENABLE_CACHE = os.getenv("OPENAI_ENABLE_CACHE", "false").lower() == "true"

# Smart summary settings
ENABLE_SMART_SUMMARIES = os.getenv("ENABLE_SMART_SUMMARIES", "true").lower() == "true"
SUMMARY_CACHE_DIR = DATA_DIR / "summary_cache"
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "gpt-4o-mini")  # Cheap model for summaries
SUMMARY_TEMPERATURE = int(os.getenv("SUMMARY_TEMPERATURE", "0"))  # Deterministic summaries
USE_SMART_RETRIEVAL = os.getenv("USE_SMART_RETRIEVAL", "true").lower() == "true"
