# Backend Documentation

## Overview

The backend is a FastAPI-based REST API that provides Retrieval-Augmented Generation (RAG) capabilities for processing ZIP files containing documents and code. It enables intelligent document ingestion, semantic search, question-answering, and automated documentation generation with advanced version management.

## Technology Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **ChromaDB** - Vector database for storing and querying document embeddings
- **LangChain** - Framework for building LLM applications
- **OpenAI** - GPT-4o-mini for chat and text-embedding-ada-002 for embeddings
- **Python 3.8+** - Programming language

## Architecture

### System Architecture

```
┌─────────────────┐
│   FastAPI App   │
│   (main.py)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │ API Router│
    │  (api.py) │
    └────┬────┘
         │
    ┌────┴──────────────────────────────────┐
    │                                         │
┌───▼────┐  ┌──────────┐  ┌──────────┐  ┌───▼────────┐
│Ingest  │  │  Query   │  │   Docs   │  │  Version   │
│Engine  │  │  Engine  │  │ Generator│  │  Manager   │
└───┬────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘
    │            │              │              │
    └────────────┴──────────────┴──────────────┘
                    │
            ┌───────▼────────┐
            │   ChromaDB     │
            │  Vectorstores  │
            └───────────────┘
```

### Module Breakdown

#### Core Modules

1. **api.py** - FastAPI router with all REST endpoints
   - Handles HTTP requests/responses
   - Request validation and error handling
   - Background task management

2. **ingest.py** - Document ingestion engine
   - ZIP file extraction and processing
   - Duplicate detection using SHA-256 hashing
   - File loading and chunking coordination
   - Vectorstore creation and updates

3. **query.py** - Question-answering system
   - RAG chain construction
   - Version-aware querying
   - Source attribution and metadata

4. **chunking.py** - Intelligent file chunking
   - File-type-specific parsing strategies
   - Python AST-based chunking
   - JavaScript/JSX function/class detection
   - Markdown heading-aware splitting

5. **version_manager.py** - Version management system
   - Version metadata tracking
   - Isolated vectorstore management
   - Version CRUD operations
   - Search and filtering

6. **documentation.py** - Standard documentation generation
   - File-by-file documentation
   - Progress tracking
   - Caching support

7. **rag_documentation.py** - RAG-enhanced documentation
   - Cross-file awareness using embeddings
   - Multiple documentation modes
   - Project overview generation

8. **config.py** - Configuration management
   - Environment variable loading
   - Directory setup
   - Default values

### Data Flow

1. **Ingestion Flow**:
   ```
   ZIP Upload → Extract → Load Files → Chunk → Generate Embeddings → Store in ChromaDB
   ```

2. **Query Flow**:
   ```
   Query → Retrieve Similar Chunks → Build Context → Generate Answer with LLM → Return Response
   ```

3. **Documentation Flow**:
   ```
   ZIP Upload → Extract → Process Files → Generate Docs → Cache → Return/Download
   ```

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- pip package manager

### Step-by-Step Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   
   Create a `.env` file in the project root or backend directory:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```
   
   The system will automatically look for `.env` files in:
   - Project root directory
   - Backend directory
   - Current working directory

5. **Run the server**:
   ```bash
   # From project root:
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or from backend directory:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Verify installation**:
   - Health check: `http://localhost:8000/api/health`
   - API docs: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings and chat | None | Yes |
| `DOCUMENTATION_MODE` | Documentation mode: standard, rag, hybrid | `standard` | No |
| `DOC_ENABLE_CACHING` | Enable documentation caching | `true` | No |
| `DOC_CACHE_TTL_HOURS` | Cache TTL in hours | `24` | No |
| `DOC_MAX_FILE_SIZE` | Maximum file size for docs (bytes) | `10485760` (10MB) | No |
| `DOC_MAX_TOKENS_PER_CHUNK` | Max tokens per documentation chunk | `4000` | No |
| `OPENAI_MAX_RETRIES` | Maximum API retry attempts | `3` | No |
| `OPENAI_TIMEOUT` | API timeout in seconds | `60` | No |
| `ENABLE_SMART_SUMMARIES` | Enable smart summary generation | `true` | No |
| `SUMMARY_MODEL` | Model for summaries | `gpt-4o-mini` | No |

### Configuration File (config.py)

Key configuration constants:

- `CHUNK_SIZE` - Default chunk size: 1000 characters
- `CHUNK_OVERLAP` - Overlap between chunks: 100 characters
- `DATA_DIR` - Directory for temporary files and data
- `VECTOR_DIR` - Default vectorstore directory
- `RAG_RETRIEVAL_K` - Number of documents to retrieve: 5

## API Documentation

### Base URL
```
http://localhost:8000/api
```

### Authentication
Currently, no authentication is required. In production, implement proper authentication.

### Endpoints

#### Ingestion Endpoints

##### `POST /api/ingest`
Basic ZIP file ingestion (legacy endpoint).

**Request**:
- Content-Type: `multipart/form-data`
- Body: ZIP file

**Response**:
```json
{
  "message": "Ingestion complete",
  "files_processed": 10,
  "chunks_created": 45,
  "filename": "project.zip"
}
```

##### `POST /api/ingest_versioned`
Upload ZIP file as a new version with metadata.

**Request**:
- Content-Type: `multipart/form-data`
- Form fields:
  - `file`: ZIP file (required)
  - `version_name`: Version name (required)
  - `description`: Description (optional)
  - `tags`: Comma-separated tags (optional)

**Response**:
```json
{
  "message": "Version created successfully",
  "version_id": "my-project-20240101-120000",
  "version_name": "my-project",
  "description": "Initial release",
  "files_processed": 10,
  "chunks_created": 45,
  "filename": "project.zip",
  "tags": ["release", "stable"],
  "upload_timestamp": "2024-01-01T12:00:00"
}
```

#### Query Endpoints

##### `GET /api/query`
Query documents using natural language.

**Query Parameters**:
- `q`: Query string (required, 1-1000 characters)
- `version_id`: Specific version ID to query (optional)

**Response**:
```json
{
  "answer": "The answer to your question...",
  "sources": [
    {
      "file": "/path/to/file.py",
      "chunk_type": "function",
      "chunk_name": "calculate_sum",
      "file_extension": ".py",
      "content_preview": "def calculate_sum(a, b):..."
    }
  ],
  "query": "How does the sum function work?",
  "version_info": {
    "version_id": "my-project-20240101-120000",
    "version_name": "my-project",
    "description": "Initial release"
  }
}
```

##### `GET /api/query_compare`
Compare answers across multiple versions.

**Query Parameters**:
- `q`: Query string (required)
- `version_ids`: Comma-separated version IDs (required, minimum 2)

**Response**:
```json
{
  "query": "How does authentication work?",
  "comparison_results": [
    {
      "version_id": "v1-20240101",
      "version_name": "v1",
      "description": "First version",
      "answer": "Answer from v1...",
      "sources_count": 3
    },
    {
      "version_id": "v2-20240201",
      "version_name": "v2",
      "description": "Second version",
      "answer": "Answer from v2...",
      "sources_count": 4
    }
  ],
  "total_versions": 2
}
```

#### Version Management Endpoints

##### `GET /api/versions`
List all versions with optional filtering.

**Query Parameters**:
- `status`: Filter by status: `active`, `archived`, `deleted` (optional)

**Response**:
```json
{
  "versions": [
    {
      "version_id": "my-project-20240101-120000",
      "version_name": "my-project",
      "description": "Initial release",
      "upload_timestamp": "2024-01-01T12:00:00",
      "file_count": 10,
      "chunk_count": 45,
      "file_types": [".py", ".js"],
      "status": "active",
      "tags": ["release", "stable"]
    }
  ],
  "total_versions": 1
}
```

##### `GET /api/versions/{version_id}`
Get detailed information about a specific version.

**Path Parameters**:
- `version_id`: Version ID

**Response**:
```json
{
  "version_id": "my-project-20240101-120000",
  "version_name": "my-project",
  "description": "Initial release",
  "upload_timestamp": "2024-01-01T12:00:00",
  "zip_filename": "project.zip",
  "file_count": 10,
  "chunk_count": 45,
  "file_types": [".py", ".js"],
  "status": "active",
  "tags": ["release", "stable"],
  "vectorstore_path": "/path/to/vectorstore"
}
```

##### `GET /api/versions/search`
Search versions by name, description, or tags.

**Query Parameters**:
- `q`: Search query (required)

**Response**:
```json
{
  "query": "stable",
  "versions": [
    {
      "version_id": "my-project-20240101-120000",
      "version_name": "my-project",
      "description": "Initial release",
      "upload_timestamp": "2024-01-01T12:00:00",
      "status": "active",
      "tags": ["release", "stable"]
    }
  ],
  "total_matches": 1
}
```



## Core Features

### ZIP File Processing

**Supported File Types**:
- `.py` - Python files
- `.js`, `.jsx` - JavaScript/React files
- `.ts`, `.tsx` - TypeScript files
- `.md`, `.txt` - Markdown and text files
- `.json`, `.yaml`, `.yml` - Configuration files
- `.html`, `.css` - Web files

**Features**:
- Maximum file size: 100MB per ZIP
- Automatic extraction and processing
- UTF-8 encoding with error handling
- Empty file filtering

### Smart Chunking

The system uses file-type-specific chunking strategies:

**Python Files**:
- AST-based parsing for functions, classes, and imports
- Preserves docstrings and signatures
- Fallback to regex-based chunking if AST fails
- Multi-tier chunking with summaries (optional)

**JavaScript/JSX Files**:
- Function and class detection using regex
- Arrow function support
- Block-level chunking

**Markdown/Text Files**:
- Heading-respecting section splitting
- Preserves document structure
- Recursive splitting for large sections

**Fallback**:
- Recursive character text splitting
- Configurable chunk size and overlap
- Smart separator selection

### Vector Storage

**ChromaDB Integration**:
- Persistent vector storage
- Version-isolated vectorstores
- Automatic persistence
- Metadata-rich document storage

**Embeddings**:
- Model: `text-embedding-ada-002`
- Dimension: 1536
- Automatic embedding generation

**Metadata Stored**:
- File source path
- Chunk type and name
- File extension
- File hash (SHA-256)
- File size and modification time
- Chunk index

### Query System

**RAG Implementation**:
- Retrieval-Augmented Generation
- Similarity search with top-k retrieval (default: 4 chunks)
- Context-aware answer generation
- Source attribution

**LLM Configuration**:
- Model: `gpt-4o-mini`
- Temperature: 0 (deterministic)
- Custom prompt templates
- Version context injection

**Features**:
- Version-specific queries
- Latest version fallback
- Multi-version comparison
- Source document previews

### Version Management

**Complete Isolation**:
- Each version has its own ChromaDB instance
- Separate vectorstore directories
- Independent metadata tracking

**Metadata Tracking**:
- Version ID (auto-generated)
- Version name
- Description
- Tags (comma-separated)
- Upload timestamp
- File and chunk counts
- File type analysis
- Status (active/archived/deleted)

**Operations**:
- Create versions with metadata
- List with filtering
- Search by name/description/tags
- Update status
- Delete versions (with cleanup)

### Documentation Generation

**Standard Documentation**:
- File-by-file analysis
- Language-specific templates
- Markdown output
- Progress tracking
- Background processing

**RAG-Enhanced Documentation**:
- Cross-file awareness
- Multiple modes:
  - `file`: Individual file documentation
  - `project`: Project-level overview
  - `api`: API-focused documentation
  - `cross-file`: Relationship analysis
- Vector-based context retrieval
- Intelligent caching (24-hour TTL)

**Caching**:
- MD5-based content hashing
- 24-hour cache TTL
- Automatic cache invalidation
- Cost reduction through caching

### Duplicate Detection

**SHA-256 Hashing**:
- Content-based duplicate detection
- Hash stored in metadata
- Automatic skipping of duplicates
- Legacy ingestion only (versioned uploads process all files)

## Development

### Project Structure

```
backend/
├── __init__.py
├── main.py              # FastAPI application entry point
├── api.py               # API router and endpoints
├── ingest.py            # Ingestion engine
├── query.py             # Query engine
├── chunking.py          # Chunking strategies
├── version_manager.py   # Version management
├── documentation.py     # Standard documentation
├── rag_documentation.py # RAG-enhanced documentation
├── config.py            # Configuration
├── doc_processor.py     # Documentation processor
├── summary_generator.py # Summary generation
├── token_manager.py     # Token management
├── utils/
│   └── openai_utils.py  # OpenAI utilities
└── requirements.txt    # Dependencies
```



## Data Storage

### Directory Structure

```
project_root/
├── data/
│   ├── versions.json          # Version metadata
│   ├── versions/              # Version vectorstores
│   │   └── {version_id}/
│   ├── documentation/         # Generated documentation
│   ├── summary_cache/         # Summary cache
│   └── unzipped/              # Temporary extraction (auto-cleaned)
├── vectorstore/               # Default vectorstore (legacy)
└── backend/
    └── ...
```

### Data Persistence

- **ChromaDB**: Automatically persists vectorstores
- **JSON Metadata**: Version metadata stored in `versions.json`
- **Cache**: Documentation cache with TTL
- **Cleanup**: Temporary files automatically removed

## Security Considerations

1. **File Upload Validation**:
   - File type validation (ZIP only)
   - File size limits (100MB)
   - Path traversal protection

2. **API Security**:
   - CORS configuration (currently allows all origins)
   - Input validation (query length, parameter types)
   - Error message sanitization

3. **Production Recommendations**:
   - Implement authentication/authorization
   - Rate limiting
   - API key management
   - HTTPS only
   - Input sanitization
   - Regular security updates

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

