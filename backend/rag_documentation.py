"""
RAG-Enhanced Documentation Generation Module
Generates documentation using ChromaDB embeddings for cross-file awareness
"""

import zipfile
import tempfile
import shutil
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document

from .config import OPENAI_API_KEY, DATA_DIR, RAG_DOCUMENTATION_CACHE, RAG_RETRIEVAL_K
from .chunking import chunk_file
from .utils.openai_utils import get_embeddings, get_chat_llm
from .ingest import ingest_zip_versioned, load_files, create_vectorstore
from .version_manager import version_manager


class DocumentationCache:
    """Simple cache for documentation generation to reduce API costs"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or DATA_DIR / "documentation_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=24)  # Cache for 24 hours
    
    def _get_cache_key(self, content: str, doc_type: str) -> str:
        """Generate cache key based on content and document type"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"{doc_type}_{content_hash}.json"
    
    def get_cached_documentation(self, content: str, doc_type: str) -> Optional[Dict[str, Any]]:
        """Get cached documentation if available and not expired"""
        if not RAG_DOCUMENTATION_CACHE:
            return None
        
        cache_key = self._get_cache_key(content, doc_type)
        cache_file = self.cache_dir / cache_key
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Check if cache is expired
            cache_time = datetime.fromisoformat(cached_data.get('timestamp', ''))
            if datetime.now() - cache_time > self.cache_ttl:
                cache_file.unlink()  # Remove expired cache
                return None
            
            return cached_data.get('documentation')
        
        except (json.JSONDecodeError, KeyError, ValueError):
            # Remove corrupted cache file
            if cache_file.exists():
                cache_file.unlink()
            return None
    
    def cache_documentation(self, content: str, doc_type: str, documentation: Dict[str, Any]):
        """Cache documentation for future use"""
        if not RAG_DOCUMENTATION_CACHE:
            return
        
        cache_key = self._get_cache_key(content, doc_type)
        cache_file = self.cache_dir / cache_key
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'documentation': documentation
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        
        except Exception as e:
            # Silently fail if caching doesn't work
            pass


class RAGDocumentationGenerator:
    """RAG-enhanced documentation generator with cross-file awareness"""
    
    def __init__(self, version_id: Optional[str] = None):
        self.version_id = version_id
        self.vectorstore = None
        self.embeddings = get_embeddings()
        self.llm = get_chat_llm(model="gpt-4o-mini", temperature=0.1)
        self.cache = DocumentationCache()
        
    def _load_vectorstore(self) -> Chroma:
        """Load the appropriate vectorstore based on version_id"""
        if self.version_id:
            version = version_manager.get_version(self.version_id)
            if not version:
                raise ValueError(f"Version {self.version_id} not found")
            vectorstore_path = version.vectorstore_path
        else:
            # Use latest version or default
            latest_version = version_manager.get_latest_version()
            if latest_version:
                vectorstore_path = latest_version.vectorstore_path
            else:
                from .config import VECTOR_DIR
                vectorstore_path = str(VECTOR_DIR)
        
        return Chroma(persist_directory=vectorstore_path, embedding_function=self.embeddings)
    
    def retrieve_related_files(self, query: str, k: int = None) -> List[Document]:
        """Retrieve related files using semantic search with caching support"""
        if not self.vectorstore:
            self.vectorstore = self._load_vectorstore()
        
        # Use configured k value if not provided
        if k is None:
            k = RAG_RETRIEVAL_K
        
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": k},
            search_type="similarity"
        )
        return retriever.get_relevant_documents(query)
    
    def find_file_dependencies(self, file_path: str) -> Dict[str, List[Document]]:
        """Find files that depend on or are depended upon by the given file"""
        dependencies = {
            "imports": [],
            "imported_by": [],
            "related_functions": [],
            "related_classes": []
        }
        
        # Find files that import this file
        import_query = f"files that import {Path(file_path).stem} from {file_path}"
        dependencies["imported_by"] = self.retrieve_related_files(import_query, k=3)
        
        # Find related functions and classes
        function_query = f"functions and classes related to {Path(file_path).stem}"
        dependencies["related_functions"] = self.retrieve_related_files(function_query, k=3)
        
        return dependencies
    
    def generate_enhanced_file_docs(self, file_path: Path, file_content: str, file_extension: str) -> Dict[str, Any]:
        """Generate enhanced file documentation with cross-file context"""
        try:
            # Check cache first
            cache_key = f"{file_path}_{file_extension}"
            cached_doc = self.cache.get_cached_documentation(cache_key, "file_docs")
            if cached_doc:
                return cached_doc
            
            # Get related files and dependencies
            dependencies = self.find_file_dependencies(str(file_path))
            
            # Build context from related files
            related_context = ""
            if dependencies["imported_by"]:
                related_context += "\n\n## Files that import this module:\n"
                for doc in dependencies["imported_by"]:
                    related_context += f"- {doc.metadata.get('source', 'Unknown')}\n"
                    related_context += f"  {doc.page_content[:200]}...\n"
            
            if dependencies["related_functions"]:
                related_context += "\n\n## Related functions and classes:\n"
                for doc in dependencies["related_functions"]:
                    related_context += f"- {doc.metadata.get('source', 'Unknown')}\n"
                    related_context += f"  {doc.page_content[:200]}...\n"
            
            # Create enhanced prompt
            if file_extension.lower() == '.py':
                prompt = f"""
                Analyze this Python file and generate comprehensive documentation with cross-file awareness:
                
                File: {file_path.name}
                Path: {file_path}
                
                Code:
                ```python
                {file_content}
                ```
                
                Related Context:
                {related_context}
                
                Please provide:
                1. **File Overview**: Brief description of what this file does
                2. **Functions**: List all functions with descriptions, parameters, and return values
                3. **Classes**: List all classes with descriptions and their methods
                4. **Imports**: Explain what external dependencies this file uses
                5. **Dependencies**: How this file relates to other files in the project
                6. **Key Features**: Main functionality and purpose
                7. **Usage Examples**: How to use the main functions/classes
                8. **Cross-file Relationships**: How this file interacts with other files
                
                Format the response as structured markdown.
                """
            else:
                prompt = f"""
                Analyze this file and generate comprehensive documentation with cross-file awareness:
                
                File: {file_path.name}
                Path: {file_path}
                Type: {file_extension}
                
                Content:
                ```
                {file_content}
                ```
                
                Related Context:
                {related_context}
                
                Please provide:
                1. **File Overview**: What this file contains
                2. **Purpose**: What this file is used for
                3. **Key Content**: Important information or functionality
                4. **Dependencies**: How this file relates to other files
                5. **Cross-file Relationships**: How this file interacts with other files
                
                Format the response as structured markdown.
                """
            
            # Generate documentation
            response = self.llm.invoke(prompt)
            documentation = response.content
            
            result = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_extension": file_extension,
                "file_size": len(file_content),
                "documentation": documentation,
                "dependencies": {
                    "imported_by_count": len(dependencies["imported_by"]),
                    "related_functions_count": len(dependencies["related_functions"])
                },
                "status": "success"
            }
            
            # Cache the result
            self.cache.cache_documentation(cache_key, "file_docs", result)
            
            return result
            
        except Exception as e:
            return {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_extension": file_extension,
                "file_size": len(file_content),
                "documentation": f"Error generating documentation: {str(e)}",
                "status": "error",
                "error": str(e)
            }
    
    def generate_project_overview(self, include_relationships: bool = True) -> Dict[str, Any]:
        """Generate high-level project architectural documentation"""
        try:
            # Check cache first
            cache_key = f"project_overview_{self.version_id or 'latest'}_{include_relationships}"
            cached_doc = self.cache.get_cached_documentation(cache_key, "project_overview")
            if cached_doc:
                return cached_doc
            
            if not self.vectorstore:
                self.vectorstore = self._load_vectorstore()
            
            # Get project structure
            structure_query = "project structure architecture main components"
            structure_docs = self.retrieve_related_files(structure_query, k=10)
            
            # Get API endpoints if any
            api_query = "API endpoints routes controllers handlers"
            api_docs = self.retrieve_related_files(api_query, k=5)
            
            # Get configuration files
            config_query = "configuration settings config files"
            config_docs = self.retrieve_related_files(config_query, k=3)
            
            # Build context
            context = "## Project Structure Analysis\n\n"
            for doc in structure_docs:
                context += f"### {doc.metadata.get('source', 'Unknown')}\n"
                context += f"{doc.page_content[:300]}...\n\n"
            
            if api_docs:
                context += "## API Endpoints\n\n"
                for doc in api_docs:
                    context += f"### {doc.metadata.get('source', 'Unknown')}\n"
                    context += f"{doc.page_content[:200]}...\n\n"
            
            if config_docs:
                context += "## Configuration\n\n"
                for doc in config_docs:
                    context += f"### {doc.metadata.get('source', 'Unknown')}\n"
                    context += f"{doc.page_content[:200]}...\n\n"
            
            prompt = f"""
            Analyze this codebase and generate comprehensive project-level architectural documentation:
            
            {context}
            
            Please provide:
            1. **Project Overview**: High-level description of what this project does
            2. **Architecture**: Main architectural patterns and components
            3. **File Organization**: How files are structured and organized
            4. **Key Components**: Main modules, classes, and functions
            5. **API Structure**: If applicable, main API endpoints and routes
            6. **Configuration**: Key configuration files and settings
            7. **Dependencies**: External libraries and internal dependencies
            8. **Data Flow**: How data flows through the system
            9. **Integration Points**: How different parts of the system connect
            10. **Deployment**: How the project is deployed and configured
            
            Format as structured markdown with clear sections.
            """
            
            response = self.llm.invoke(prompt)
            documentation = response.content
            
            result = {
                "documentation": documentation,
                "analysis_stats": {
                    "structure_files": len(structure_docs),
                    "api_files": len(api_docs),
                    "config_files": len(config_docs)
                },
                "status": "success"
            }
            
            # Cache the result
            self.cache.cache_documentation(cache_key, "project_overview", result)
            
            return result
            
        except Exception as e:
            return {
                "documentation": f"Error generating project overview: {str(e)}",
                "status": "error",
                "error": str(e)
            }
    
    def generate_api_documentation(self) -> Dict[str, Any]:
        """Generate comprehensive API documentation by aggregating endpoints"""
        try:
            # Check cache first
            cache_key = f"api_documentation_{self.version_id or 'latest'}"
            cached_doc = self.cache.get_cached_documentation(cache_key, "api_documentation")
            if cached_doc:
                return cached_doc
            
            if not self.vectorstore:
                self.vectorstore = self._load_vectorstore()
            
            # Find all API-related content
            api_queries = [
                "API endpoints routes handlers",
                "FastAPI router endpoints",
                "HTTP methods GET POST PUT DELETE",
                "request response models",
                "authentication authorization"
            ]
            
            all_api_docs = []
            for query in api_queries:
                docs = self.retrieve_related_files(query, k=5)
                all_api_docs.extend(docs)
            
            # Remove duplicates
            seen_sources = set()
            unique_docs = []
            for doc in all_api_docs:
                source = doc.metadata.get('source', '')
                if source not in seen_sources:
                    seen_sources.add(source)
                    unique_docs.append(doc)
            
            # Build context
            context = "## API Documentation Analysis\n\n"
            for doc in unique_docs:
                context += f"### {doc.metadata.get('source', 'Unknown')}\n"
                context += f"```{doc.metadata.get('file_extension', '')}\n"
                context += f"{doc.page_content}\n```\n\n"
            
            prompt = f"""
            Analyze this API code and generate comprehensive API documentation:
            
            {context}
            
            Please provide:
            1. **API Overview**: What this API does and its purpose
            2. **Base URL and Versioning**: API base URL and versioning strategy
            3. **Authentication**: How to authenticate with the API
            4. **Endpoints**: Complete list of all endpoints with:
               - HTTP method and path
               - Description
               - Request parameters
               - Request body schema
               - Response schema
               - Status codes
            5. **Data Models**: Request and response data models
            6. **Error Handling**: Error responses and status codes
            7. **Rate Limiting**: Any rate limiting information
            8. **Examples**: Usage examples for key endpoints
            
            Format as structured markdown with clear sections and code examples.
            """
            
            response = self.llm.invoke(prompt)
            documentation = response.content
            
            result = {
                "documentation": documentation,
                "endpoints_analyzed": len(unique_docs),
                "status": "success"
            }
            
            # Cache the result
            self.cache.cache_documentation(cache_key, "api_documentation", result)
            
            return result
            
        except Exception as e:
            return {
                "documentation": f"Error generating API documentation: {str(e)}",
                "status": "error",
                "error": str(e)
            }


def generate_rag_documentation(
    zip_path: Path, 
    mode: str = "file",
    version_id: Optional[str] = None,
    save_as_files: bool = True
) -> Dict[str, Any]:
    """
    Main entry point for RAG-enhanced documentation generation
    
    Args:
        zip_path: Path to ZIP file to process
        mode: Documentation mode - "file", "project", "api", "cross-file"
        version_id: Optional version ID to use existing vectorstore
        save_as_files: Whether to save documentation as markdown files
    """
    try:
        generator = RAGDocumentationGenerator(version_id)
        
        if mode == "project":
            # Generate project overview
            result = generator.generate_project_overview()
            
            if save_as_files and result["status"] == "success":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = DATA_DIR / "documentation" / f"rag_docs_{timestamp}"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Save project overview
                overview_path = output_dir / "project_overview.md"
                with open(overview_path, 'w', encoding='utf-8') as f:
                    f.write(result["documentation"])
                
                result["output_directory"] = str(output_dir)
                result["generated_files"] = [str(overview_path)]
                
                # Add download ID
                from .documentation import extract_download_id_from_path
                result["download_id"] = extract_download_id_from_path(str(output_dir))
            
            return result
            
        elif mode == "api":
            # Generate API documentation
            result = generator.generate_api_documentation()
            
            if save_as_files and result["status"] == "success":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = DATA_DIR / "documentation" / f"rag_docs_{timestamp}"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Save API documentation
                api_path = output_dir / "api_documentation.md"
                with open(api_path, 'w', encoding='utf-8') as f:
                    f.write(result["documentation"])
                
                result["output_directory"] = str(output_dir)
                result["generated_files"] = [str(api_path)]
                
                # Add download ID
                from .documentation import extract_download_id_from_path
                result["download_id"] = extract_download_id_from_path(str(output_dir))
            
            return result
            
        else:
            # File-level or cross-file documentation
            # First, ingest the ZIP if no version_id provided
            if not version_id:
                # Create a temporary version for this documentation
                temp_version_name = f"doc_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                version_metadata, _, _ = ingest_zip_versioned(
                    zip_path, temp_version_name, "Temporary version for documentation generation"
                )
                version_id = version_metadata.version_id
                generator.version_id = version_id
            
            # Extract and process files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                extract_to = temp_path / "extracted"
                extract_to.mkdir()
                
                # Extract ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                
                # Find files to document
                supported_extensions = ['.py', '.js', '.jsx', '.md', '.txt', '.json', '.yaml', '.yml', '.html', '.css']
                files_to_document = []
                for file_path in extract_to.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                        files_to_document.append(file_path)
                
                if not files_to_document:
                    return {
                        "status": "error",
                        "message": "No supported files found in ZIP archive",
                        "files_processed": 0
                    }
                
                # Generate documentation for each file
                documentations = []
                successful_docs = 0
                failed_docs = 0
                generated_files = []
                
                for file_path in files_to_document:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if content.strip():
                            doc_result = generator.generate_enhanced_file_docs(
                                file_path.relative_to(extract_to),
                                content,
                                file_path.suffix
                            )
                            
                            if save_as_files and doc_result["status"] == "success":
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                output_dir = DATA_DIR / "documentation" / f"rag_docs_{timestamp}"
                                output_dir.mkdir(parents=True, exist_ok=True)
                                
                                md_filename = f"{file_path.stem}_rag_documentation.md"
                                md_path = output_dir / md_filename
                                
                                with open(md_path, 'w', encoding='utf-8') as f:
                                    f.write(doc_result["documentation"])
                                
                                doc_result["markdown_file"] = str(md_path)
                                generated_files.append(str(md_path))
                            
                            documentations.append(doc_result)
                            
                            if doc_result["status"] == "success":
                                successful_docs += 1
                            else:
                                failed_docs += 1
                    
                    except Exception as e:
                        documentations.append({
                            "file_path": str(file_path.relative_to(extract_to)),
                            "file_name": file_path.name,
                            "file_extension": file_path.suffix,
                            "documentation": f"Error processing file: {str(e)}",
                            "status": "error",
                            "error": str(e)
                        })
                        failed_docs += 1
                
            # Extract download ID for the download endpoint
            from .documentation import extract_download_id_from_path
            download_id = extract_download_id_from_path(str(output_dir)) if save_as_files else None
            
            return {
                "status": "success",
                "message": f"RAG documentation generated for {len(files_to_document)} files",
                "mode": mode,
                "files_processed": len(files_to_document),
                "successful_documentations": successful_docs,
                "failed_documentations": failed_docs,
                "documentations": documentations,
                "generated_files": generated_files if save_as_files else [],
                "download_id": download_id
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error generating RAG documentation: {str(e)}",
            "error": str(e)
        }
