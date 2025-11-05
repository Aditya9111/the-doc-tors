import zipfile
import shutil
import hashlib
import os
from pathlib import Path
from typing import List, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .utils.openai_utils import get_embeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from .config import DATA_DIR, VECTOR_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from .chunking import chunk_file
from .version_manager import version_manager, VersionMetadata


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of file content"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"Warning: Could not calculate hash for {file_path}: {e}")
        return ""


def get_existing_files_metadata() -> dict:
    """Get metadata of existing files in vectorstore"""
    existing_files = {}
    
    try:
        if not os.path.exists(VECTOR_DIR):
            return existing_files
            
        # Load existing vectorstore to check metadata
        embeddings = get_embeddings()
        vectorstore = Chroma(persist_directory=str(VECTOR_DIR), embedding_function=embeddings)
        
        # Get all documents from the collection
        collection = vectorstore._collection
        if collection.count() > 0:
            results = collection.get(include=["metadatas"])
            
            for metadata in results.get("metadatas", []):
                source = metadata.get("source", "")
                file_hash = metadata.get("file_hash", "")
                if source and file_hash:
                    existing_files[source] = {
                        "hash": file_hash,
                        "chunk_type": metadata.get("chunk_type", ""),
                        "chunk_name": metadata.get("chunk_name", ""),
                        "file_extension": metadata.get("file_extension", "")
                    }
                    
    except Exception as e:
        print(f"Warning: Could not load existing files metadata: {e}")
    
    return existing_files


def is_file_duplicate(file_path: Path, existing_files: dict) -> bool:
    """Check if file is a duplicate based on content hash"""
    file_hash = calculate_file_hash(file_path)
    if not file_hash:
        return False
    
    # Check if any existing file has the same hash
    for existing_source, existing_metadata in existing_files.items():
        if existing_metadata["hash"] == file_hash:
            return True
    
    return False


def remove_duplicate_documents(vectorstore, file_path: Path):
    """Remove documents from vectorstore that match the given file"""
    try:
        collection = vectorstore._collection
        
        # Get all document IDs and metadata
        results = collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", [])
        ids = results.get("ids", [])
        
        # Find IDs to delete
        ids_to_delete = []
        for i, metadata in enumerate(metadatas):
            if metadata.get("source") == str(file_path):
                ids_to_delete.append(ids[i])
        
        # Delete duplicate documents
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            print(f"Removed {len(ids_to_delete)} duplicate documents for {file_path}")
            
    except Exception as e:
        print(f"Warning: Could not remove duplicates for {file_path}: {e}")


def extract_zip(zip_path: Path, extract_to: Path):
    """Extract ZIP file to specified directory"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except zipfile.BadZipFile:
        raise ValueError(f"Invalid ZIP file: {zip_path}")
    except Exception as e:
        raise Exception(f"Error extracting ZIP file: {str(e)}")


def load_files(folder: Path, existing_files: dict = None):
    """Load and process files from directory with duplicate detection"""
    docs = []
    duplicates_skipped = 0
    supported_extensions = [".txt", ".py", ".js", ".jsx", ".md", ".json", ".yaml", ".yml", ".xml", ".html", ".css"]
    
    if existing_files is None:
        existing_files = {}
    
    for file in folder.rglob("*"):
        if file.is_file() and file.suffix.lower() in supported_extensions:
            try:
                # Check for duplicates
                if is_file_duplicate(file, existing_files):
                    print(f"⏭️  Skipping duplicate file: {file.name}")
                    duplicates_skipped += 1
                    continue
                
                with open(file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if content.strip():  # Only process non-empty files
                        # Calculate file hash for future duplicate detection
                        file_hash = calculate_file_hash(file)
                        
                        # Use advanced chunking based on file type
                        chunks = chunk_file(content, file.suffix)
                        
                        # Convert chunks to Document objects
                        for i, chunk in enumerate(chunks):
                            if isinstance(chunk, dict):
                                chunk_content = chunk.get("content", "")
                                chunk_type = chunk.get("type", "unknown")
                                chunk_name = chunk.get("name", "")
                            else:
                                chunk_content = str(chunk)
                                chunk_type = "text"
                                chunk_name = ""
                            
                            if chunk_content.strip():
                                metadata = {
                                    "source": str(file),
                                    "chunk_index": i,
                                    "chunk_type": chunk_type,
                                    "chunk_name": chunk_name,
                                    "file_extension": file.suffix,
                                    "file_hash": file_hash,
                                    "file_size": file.stat().st_size,
                                    "file_modified": file.stat().st_mtime
                                }
                                docs.append(Document(page_content=chunk_content, metadata=metadata))
            except Exception as e:
                print(f"Warning: Could not process file {file}: {str(e)}")
                continue
    
    if duplicates_skipped > 0:
        print(f"📊 Skipped {duplicates_skipped} duplicate files")
    
    return docs


def chunk_documents_fallback(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Fallback chunking for documents that weren't processed by advanced chunking"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_documents(documents)


def create_vectorstore(docs, vectorstore_path: str = None):
    """Create and persist vector store"""
    try:
        embeddings = get_embeddings()
        persist_dir = vectorstore_path or str(VECTOR_DIR)
        
        vectorstore = Chroma.from_documents(
            docs, 
            embeddings, 
            persist_directory=persist_dir
        )
        return vectorstore
    except Exception as e:
        raise Exception(f"Error creating vector store: {str(e)}")


def update_vectorstore(docs, vectorstore_path: str = None):
    """Update existing vector store with new documents"""
    try:
        embeddings = get_embeddings()
        persist_dir = vectorstore_path or str(VECTOR_DIR)
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
        
        # Add new documents to existing vectorstore
        vectorstore.add_documents(docs)
        
        return vectorstore
    except Exception as e:
        raise Exception(f"Error updating vector store: {str(e)}")


def ingest_zip(zip_file: Path):
    """Main ingestion function with duplicate detection (legacy - for backward compatibility)"""
    try:
        # Get existing files metadata for duplicate detection
        existing_files = get_existing_files_metadata()
        print(f"📋 Found {len(existing_files)} existing files in vectorstore")
        
        # Clean up previous extraction
        extract_to = DATA_DIR / "unzipped"
        if extract_to.exists():
            shutil.rmtree(extract_to)
        extract_to.mkdir(exist_ok=True)
        
        # Extract ZIP file
        extract_zip(zip_file, extract_to)
        
        # Load and process files with duplicate detection
        raw_docs = load_files(extract_to, existing_files)
        
        if not raw_docs:
            print("⚠️  No new files to process (all files were duplicates)")
            # Clean up extracted files
            shutil.rmtree(extract_to)
            return 0, 0
        
        # Create or update vector store
        if existing_files:
            # Update existing vectorstore
            vectorstore = update_vectorstore(raw_docs)
        else:
            # Create new vectorstore
            vectorstore = create_vectorstore(raw_docs)
        
        # Clean up extracted files
        shutil.rmtree(extract_to)
        
        return len(raw_docs), len(raw_docs)  # Return count of documents and chunks
        
    except Exception as e:
        # Clean up on error
        extract_to = DATA_DIR / "unzipped"
        if extract_to.exists():
            shutil.rmtree(extract_to)
        raise e


def ingest_zip_versioned(
    zip_file: Path,
    version_name: str,
    description: str = "",
    tags: List[str] = None
) -> Tuple[VersionMetadata, int, int]:
    """Ingest ZIP file as a new version with complete separation"""
    try:
        # Clean up previous extraction
        extract_to = DATA_DIR / "unzipped"
        if extract_to.exists():
            shutil.rmtree(extract_to)
        extract_to.mkdir(exist_ok=True)
        
        # Extract ZIP file
        extract_zip(zip_file, extract_to)
        
        # Load and process files (no duplicate detection for versioned uploads)
        raw_docs = load_files(extract_to, existing_files={})
        
        if not raw_docs:
            print("⚠️  No files to process")
            shutil.rmtree(extract_to)
            raise ValueError("No processable files found in ZIP archive")
        
        # Get file types from processed documents
        file_types = list(set(doc.metadata.get("file_extension", "") for doc in raw_docs))
        
        # Create version metadata
        version_metadata = version_manager.create_version_metadata(
            version_name=version_name,
            description=description,
            zip_filename=zip_file.name,
            file_count=len(set(doc.metadata.get("source", "") for doc in raw_docs)),
            chunk_count=len(raw_docs),
            file_types=file_types,
            tags=tags or []
        )
        
        # Create version-specific vectorstore
        vectorstore = create_vectorstore(raw_docs, version_metadata.vectorstore_path)
        
        # Save version metadata
        if not version_manager.save_version_metadata(version_metadata):
            raise Exception("Failed to save version metadata")
        
        # Clean up extracted files
        shutil.rmtree(extract_to)
        
        print(f"✅ Created version: {version_metadata.version_id}")
        print(f"📁 Vectorstore: {version_metadata.vectorstore_path}")
        print(f"📊 Files: {version_metadata.file_count}, Chunks: {version_metadata.chunk_count}")
        
        return version_metadata, version_metadata.file_count, version_metadata.chunk_count
        
    except Exception as e:
        # Clean up on error
        extract_to = DATA_DIR / "unzipped"
        if extract_to.exists():
            shutil.rmtree(extract_to)
        raise e
