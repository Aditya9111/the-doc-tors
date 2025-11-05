from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import os
import uuid
import zipfile
from typing import List, Optional
from .ingest import ingest_zip, ingest_zip_versioned
from .query import answer_question, compare_versions
from .config import DATA_DIR
from .version_manager import version_manager
from .documentation import generate_zip_documentation, create_documentation_zip, extract_download_id_from_path
from .rag_documentation import generate_rag_documentation, RAGDocumentationGenerator

router = APIRouter()

# In-memory progress tracking
documentation_progress = {}

class ProgressInfo:
    def __init__(self, total_files):
        self.total_files = total_files
        self.completed_files = 0
        self.status = "processing"  # processing, completed, error
        self.result = None
        self.error = None

def count_files_in_zip(zip_path: Path) -> int:
    """Count supported files in ZIP archive"""
    supported_extensions = ['.py', '.js', '.jsx', '.txt', '.json', '.yaml', '.yml', '.html', '.css', '.ts', '.tsx']
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        count = 0
        for file_info in zip_ref.filelist:
            if not file_info.is_dir() and file_info.filename:
                file_ext = Path(file_info.filename).suffix.lower()
                if file_ext in supported_extensions:
                    count += 1
    return count

def generate_docs_with_progress(zip_path: Path, save_as_files: bool, job_id: str):
    """Background task to generate documentation with progress tracking"""
    try:
        progress = documentation_progress[job_id]
        
        # Modified generate_zip_documentation to accept progress callback
        def update_progress():
            progress.completed_files += 1
        
        result = generate_zip_documentation(
            zip_path, 
            save_as_files,
            progress_callback=update_progress
        )
        
        progress.status = "completed"
        progress.result = result
        
    except Exception as e:
        progress = documentation_progress[job_id]
        progress.status = "error"
        progress.error = str(e)
    finally:
        # Clean up uploaded file
        if zip_path.exists():
            os.remove(zip_path)

@router.post("/ingest")
async def ingest_endpoint(file: UploadFile = File(...)):
    """Ingest a ZIP file containing documents"""
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.zip'):
            raise HTTPException(status_code=400, detail="File must be a ZIP archive")
        
        # Generate unique filename to avoid conflicts
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        zip_path = DATA_DIR / unique_filename
        
        # Save uploaded file
        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate file size (max 100MB)
        if len(content) > 100 * 1024 * 1024:
            os.remove(zip_path)
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 100MB")
        
        # Process the ZIP file
        num_files, num_chunks = ingest_zip(zip_path)
        
        # Clean up uploaded file
        os.remove(zip_path)
        
        return {
            "message": "Ingestion complete", 
            "files_processed": num_files, 
            "chunks_created": num_chunks,
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if 'zip_path' in locals() and zip_path.exists():
            os.remove(zip_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/ingest_zip")
async def ingest_zip_endpoint(file: UploadFile = File(...)):
    """Alternative endpoint name for ZIP ingestion"""
    return await ingest_endpoint(file)

@router.post("/ingest_versioned")
async def ingest_versioned_endpoint(
    file: UploadFile = File(...),
    version_name: str = Form(...),
    description: str = Form(""),
    tags: str = Form("")
):
    """Upload ZIP file as a new version with complete separation"""
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.zip'):
            raise HTTPException(status_code=400, detail="File must be a ZIP archive")
        
        # Generate unique filename to avoid conflicts
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        zip_path = DATA_DIR / unique_filename
        
        # Save uploaded file
        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate file size (max 100MB)
        if len(content) > 100 * 1024 * 1024:
            os.remove(zip_path)
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 100MB")
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        # Process the ZIP file as a new version
        version_metadata, file_count, chunk_count = ingest_zip_versioned(
            zip_path, version_name, description, tag_list
        )
        
        # Clean up uploaded file
        os.remove(zip_path)
        
        return {
            "message": "Version created successfully",
            "version_id": version_metadata.version_id,
            "version_name": version_metadata.version_name,
            "description": version_metadata.description,
            "files_processed": file_count,
            "chunks_created": chunk_count,
            "filename": file.filename,
            "tags": version_metadata.tags,
            "upload_timestamp": version_metadata.upload_timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if 'zip_path' in locals() and zip_path.exists():
            os.remove(zip_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/query")
async def query_endpoint(
    q: str = Query(..., min_length=1, max_length=1000),
    version_id: Optional[str] = Query(None, description="Specific version ID to query")
):
    """Query the ingested documents"""
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = answer_question(q, version_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.get("/query_compare")
async def query_compare_endpoint(
    q: str = Query(..., min_length=1, max_length=1000),
    version_ids: str = Query(..., description="Comma-separated version IDs to compare")
):
    """Compare answers across multiple versions"""
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        version_id_list = [vid.strip() for vid in version_ids.split(",") if vid.strip()]
        if len(version_id_list) < 2:
            raise HTTPException(status_code=400, detail="At least 2 version IDs required for comparison")
        
        result = compare_versions(q, version_id_list)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing comparison: {str(e)}")

@router.get("/versions")
async def list_versions_endpoint(status: Optional[str] = Query(None, description="Filter by status")):
    """List all versions"""
    try:
        versions = version_manager.list_versions(status)
        return {
            "versions": [
                {
                    "version_id": v.version_id,
                    "version_name": v.version_name,
                    "description": v.description,
                    "upload_timestamp": v.upload_timestamp,
                    "file_count": v.file_count,
                    "chunk_count": v.chunk_count,
                    "file_types": v.file_types,
                    "status": v.status,
                    "tags": v.tags
                }
                for v in versions
            ],
            "total_versions": len(versions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing versions: {str(e)}")

@router.get("/versions/{version_id}")
async def get_version_endpoint(version_id: str):
    """Get specific version details"""
    try:
        version = version_manager.get_version(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return {
            "version_id": version.version_id,
            "version_name": version.version_name,
            "description": version.description,
            "upload_timestamp": version.upload_timestamp,
            "zip_filename": version.zip_filename,
            "file_count": version.file_count,
            "chunk_count": version.chunk_count,
            "file_types": version.file_types,
            "status": version.status,
            "tags": version.tags,
            "vectorstore_path": version.vectorstore_path
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting version: {str(e)}")

@router.get("/versions/search")
async def search_versions_endpoint(q: str = Query(..., description="Search query")):
    """Search versions by name, description, or tags"""
    try:
        versions = version_manager.search_versions(q)
        return {
            "query": q,
            "versions": [
                {
                    "version_id": v.version_id,
                    "version_name": v.version_name,
                    "description": v.description,
                    "upload_timestamp": v.upload_timestamp,
                    "status": v.status,
                    "tags": v.tags
                }
                for v in versions
            ],
            "total_matches": len(versions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching versions: {str(e)}")

@router.put("/versions/{version_id}/status")
async def update_version_status_endpoint(
    version_id: str,
    status: str = Form(..., description="New status")
):
    """Update version status"""
    try:
        if status not in ["active", "archived", "deleted"]:
            raise HTTPException(status_code=400, detail="Invalid status. Must be: active, archived, or deleted")
        
        success = version_manager.update_version_status(version_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return {"message": f"Version {version_id} status updated to {status}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating version status: {str(e)}")

@router.delete("/versions/{version_id}")
async def delete_version_endpoint(version_id: str):
    """Delete a version and its vectorstore"""
    try:
        success = version_manager.delete_version(version_id)
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return {"message": f"Version {version_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting version: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "RAG API is running"}

@router.post("/generate_documentation")
async def generate_documentation_endpoint(
    file: UploadFile = File(...),
    save_as_files: bool = Form(True, description="Save documentation as markdown files"),
    background_tasks: BackgroundTasks = None
):
    """Generate documentation for each file in a ZIP archive with progress tracking"""
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.zip'):
            raise HTTPException(status_code=400, detail="File must be a ZIP archive")
        
        # Generate unique filename to avoid conflicts
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        zip_path = DATA_DIR / unique_filename
        
        # Save uploaded file
        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate file size (max 100MB)
        if len(content) > 100 * 1024 * 1024:
            os.remove(zip_path)
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 100MB")
        
        # Count files first
        total_files = count_files_in_zip(zip_path)
        
        if total_files == 0:
            os.remove(zip_path)
            raise HTTPException(status_code=400, detail="No supported files found in ZIP archive")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Initialize progress
        documentation_progress[job_id] = ProgressInfo(total_files)
        
        # Run in background
        background_tasks.add_task(
            generate_docs_with_progress,
            zip_path, save_as_files, job_id
        )
        
        return {
            "job_id": job_id,
            "total_files": total_files,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if 'zip_path' in locals() and zip_path.exists():
            os.remove(zip_path)
        raise HTTPException(status_code=500, detail=f"Error generating documentation: {str(e)}")

@router.get("/documentation_progress/{job_id}")
async def get_documentation_progress(job_id: str):
    """Get progress status for a documentation generation job"""
    if job_id not in documentation_progress:
        raise HTTPException(status_code=404, detail="Job not found")
    
    progress = documentation_progress[job_id]
    return {
        "total_files": progress.total_files,
        "completed_files": progress.completed_files,
        "status": progress.status,
        "result": progress.result if progress.status == "completed" else None,
        "error": progress.error if progress.status == "error" else None
    }

@router.post("/generate_documentation_rag")
async def generate_documentation_rag_endpoint(
    file: UploadFile = File(...),
    mode: str = Form("file", description="Documentation mode: file, project, api, cross-file"),
    version_id: Optional[str] = Form(None, description="Specific version ID to use"),
    save_as_files: bool = Form(True, description="Save documentation as markdown files")
):
    """Generate RAG-enhanced documentation with cross-file awareness"""
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.zip'):
            raise HTTPException(status_code=400, detail="File must be a ZIP archive")
        
        # Validate mode
        valid_modes = ["file", "project", "api", "cross-file"]
        if mode not in valid_modes:
            raise HTTPException(status_code=400, detail=f"Invalid mode. Must be one of: {', '.join(valid_modes)}")
        
        # Generate unique filename to avoid conflicts
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        zip_path = DATA_DIR / unique_filename
        
        # Save uploaded file
        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate file size (max 100MB)
        if len(content) > 100 * 1024 * 1024:
            os.remove(zip_path)
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 100MB")
        
        # Generate RAG documentation
        result = generate_rag_documentation(zip_path, mode, version_id, save_as_files)
        
        # Clean up uploaded file
        os.remove(zip_path)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if 'zip_path' in locals() and zip_path.exists():
            os.remove(zip_path)
        raise HTTPException(status_code=500, detail=f"Error generating RAG documentation: {str(e)}")

@router.post("/generate_project_overview")
async def generate_project_overview_endpoint(
    version_id: str = Form(..., description="Version ID to generate overview for"),
    include_relationships: bool = Form(True, description="Include cross-file relationships")
):
    """Generate project-level architectural documentation"""
    try:
        generator = RAGDocumentationGenerator(version_id)
        result = generator.generate_project_overview(include_relationships)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating project overview: {str(e)}")

@router.get("/download_documentation/{doc_id}")
async def download_documentation_endpoint(doc_id: str):
    """Download generated documentation as a ZIP file"""
    try:
        # Validate doc_id to prevent path traversal attacks
        if not doc_id or ".." in doc_id or "/" in doc_id or "\\" in doc_id:
            raise HTTPException(status_code=400, detail="Invalid document ID")
        
        # Look for documentation directories with this timestamp
        docs_dir = DATA_DIR / "documentation"
        if not docs_dir.exists():
            raise HTTPException(status_code=404, detail="Documentation directory not found")
        
        # Try to find the documentation directory
        doc_dirs = []
        for pattern in ["docs_*", "rag_docs_*"]:
            doc_dirs.extend(docs_dir.glob(pattern))
        
        target_dir = None
        for doc_dir in doc_dirs:
            if doc_id in doc_dir.name:
                target_dir = doc_dir
                break
        
        if not target_dir or not target_dir.exists():
            raise HTTPException(status_code=404, detail="Documentation not found")
        
        # Create ZIP file
        zip_path = create_documentation_zip(target_dir)
        
        # Return the ZIP file
        return FileResponse(
            path=str(zip_path),
            filename=f"documentation_{doc_id}.zip",
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=documentation_{doc_id}.zip"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating download: {str(e)}")

@router.get("/download_documentation_file/{doc_id}/{filename}")
async def download_single_documentation_file(doc_id: str, filename: str):
    """Download a single generated markdown file"""
    try:
        # Validate doc_id and filename to prevent path traversal attacks
        if not doc_id or ".." in doc_id or "/" in doc_id or "\\" in doc_id:
            raise HTTPException(status_code=400, detail="Invalid document ID")
        
        if not filename or ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Ensure filename ends with .md
        if not filename.lower().endswith('.md'):
            raise HTTPException(status_code=400, detail="Only markdown files can be downloaded")
        
        # Look for documentation directories with this timestamp
        docs_dir = DATA_DIR / "documentation"
        if not docs_dir.exists():
            raise HTTPException(status_code=404, detail="Documentation directory not found")
        
        # Try to find the documentation directory
        doc_dirs = []
        for pattern in ["docs_*", "rag_docs_*"]:
            doc_dirs.extend(docs_dir.glob(pattern))
        
        target_dir = None
        for doc_dir in doc_dirs:
            if doc_id in doc_dir.name:
                target_dir = doc_dir
                break
        
        if not target_dir or not target_dir.exists():
            raise HTTPException(status_code=404, detail="Documentation not found")
        
        # Look for the specific file
        file_path = target_dir / filename
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return the markdown file
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@router.get("/stats")
async def get_stats():
    """Get ingestion statistics"""
    try:
        vector_dir = DATA_DIR.parent / "vectorstore"
        if vector_dir.exists():
            # Count files in vectorstore directory
            file_count = len([f for f in vector_dir.rglob("*") if f.is_file()])
            
            # Get detailed vectorstore statistics
            try:
                from .ingest import get_existing_files_metadata
                existing_files = get_existing_files_metadata()
                
                # Count unique files by hash
                unique_hashes = set()
                for file_data in existing_files.values():
                    unique_hashes.add(file_data.get("hash", ""))
                
                return {
                    "vectorstore_exists": True,
                    "vectorstore_files": file_count,
                    "data_directory": str(DATA_DIR),
                    "total_documents": len(existing_files),
                    "unique_files": len(unique_hashes),
                    "duplicate_files": len(existing_files) - len(unique_hashes),
                    "file_types": list(set(data.get("file_extension", "") for data in existing_files.values()))
                }
            except Exception as e:
                return {
                    "vectorstore_exists": True,
                    "vectorstore_files": file_count,
                    "data_directory": str(DATA_DIR),
                    "error": f"Could not get detailed stats: {str(e)}"
                }
        else:
            return {
                "vectorstore_exists": False,
                "message": "No documents have been ingested yet"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
