"""
Documentation Generation Module
Generates documentation for each file in a ZIP archive using efficient processing
"""

import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from .config import DATA_DIR
from .doc_processor import DocumentationProcessor


def generate_file_documentation(file_path: Path, file_content: str, file_extension: str) -> Dict[str, Any]:
    """Generate documentation for a single file using efficient processor"""
    from .config import DOC_ENABLE_CACHING
    
    # Use new efficient processor if caching is enabled
    if DOC_ENABLE_CACHING:
        processor = DocumentationProcessor()
        
        # Process file with the new efficient processor
        result = processor.process_file(str(file_path), file_content)
        
        # Convert result to expected format
        return {
            "status": result["status"],
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_extension": file_extension,
            "file_size": len(file_content),
            "documentation": result.get("documentation"),
            "error": result.get("error"),
            "strategy": result.get("strategy"),
            "tokens": result.get("tokens"),
            "processing_time": result.get("processing_time"),
            "cached": result.get("cached", False)
        }
    else:
        # Fallback to original simple implementation
        return generate_file_documentation_simple(file_path, file_content, file_extension)


def generate_file_documentation_simple(file_path: Path, file_content: str, file_extension: str) -> Dict[str, Any]:
    """Original simple documentation generation (fallback)"""
    from .utils.openai_utils import get_chat_llm
    
    try:
        llm = get_chat_llm(model="gpt-4o-mini", temperature=0.1)
        
        # Simple prompt for basic documentation
        prompt = f"""
        Analyze this file and generate documentation:
        
        File: {file_path.name}
        Type: {file_extension}
        
        Content:
        ```
        {file_content[:2000]}...
        ```
        
        Please provide:
        1. **File Overview**: What this file contains
        2. **Purpose**: What this file is used for
        3. **Key Content**: Important information or functionality
        
        Format the response as structured markdown.
        """
        
        # Generate documentation
        response = llm.invoke(prompt)
        documentation = response.content
        
        return {
            "status": "success",
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_extension": file_extension,
            "file_size": len(file_content),
            "documentation": documentation,
            "strategy": "simple",
            "cached": False
        }
        
    except Exception as e:
        return {
            "status": "error",
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_extension": file_extension,
            "file_size": len(file_content),
            "documentation": f"Error generating documentation: {str(e)}",
            "error": str(e),
            "strategy": "simple",
            "cached": False
        }


def save_documentation_as_md(doc_content: str, file_path: Path, output_dir: Path) -> Path:
    """Save documentation content as a markdown file"""
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate markdown filename
    md_filename = f"{file_path.stem}_documentation.md"
    md_path = output_dir / md_filename
    
    # Write documentation to markdown file
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    return md_path


def generate_zip_documentation(zip_path: Path, save_as_files: bool = True, progress_callback = None) -> Dict[str, Any]:
    """Generate documentation for all files in a ZIP archive"""
    try:
        # Create documentation output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        docs_output_dir = DATA_DIR / "documentation" / f"docs_{timestamp}"
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_to = temp_path / "extracted"
            extract_to.mkdir()
            
            # Extract ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            # Supported file extensions for documentation
            supported_extensions = ['.py', '.js', '.jsx', '.txt', '.json', '.yaml', '.yml', '.html', '.css', '.ts', '.tsx']
            
            # Find all supported files
            files_to_document = []
            for file_path in extract_to.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    files_to_document.append(file_path)
            
            if not files_to_document:
                return {
                    "status": "error",
                    "message": "No supported files found in ZIP archive",
                    "supported_extensions": supported_extensions,
                    "files_processed": 0,
                    "documentations": [],
                    "output_directory": None
                }
            
            # Generate documentation for each file
            documentations = []
            successful_docs = 0
            failed_docs = 0
            generated_files = []
            
            for file_path in files_to_document:
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    if content.strip():  # Only process non-empty files
                        # Generate documentation
                        doc_result = generate_file_documentation(
                            file_path.relative_to(extract_to),
                            content,
                            file_path.suffix
                        )
                        
                        # Save as markdown file if requested
                        if save_as_files and doc_result["status"] == "success":
                            try:
                                md_path = save_documentation_as_md(
                                    doc_result["documentation"],
                                    file_path.relative_to(extract_to),
                                    docs_output_dir
                                )
                                doc_result["markdown_file"] = str(md_path)
                                doc_result["markdown_filename"] = md_path.name
                                generated_files.append(str(md_path))
                            except Exception as e:
                                doc_result["markdown_file"] = None
                                doc_result["markdown_error"] = str(e)
                        
                        documentations.append(doc_result)
                        
                        if doc_result["status"] == "success":
                            successful_docs += 1
                        else:
                            failed_docs += 1
                    else:
                        documentations.append({
                            "file_path": str(file_path.relative_to(extract_to)),
                            "file_name": file_path.name,
                            "file_extension": file_path.suffix,
                            "file_size": 0,
                            "documentation": "File is empty",
                            "status": "skipped",
                            "markdown_file": None
                        })
                    
                    # Update progress after each file
                    if progress_callback:
                        progress_callback()
                        
                except Exception as e:
                    documentations.append({
                        "file_path": str(file_path.relative_to(extract_to)),
                        "file_name": file_path.name,
                        "file_extension": file_path.suffix,
                        "file_size": 0,
                        "documentation": f"Error reading file: {str(e)}",
                        "status": "error",
                        "error": str(e),
                        "markdown_file": None
                    })
                    failed_docs += 1
            
            # Create index file if markdown files were generated
            if save_as_files and generated_files:
                index_content = f"""# Generated Documentation

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Source ZIP: {zip_path.name}

## Files Processed: {len(files_to_document)}
- ✅ Successful: {successful_docs}
- ❌ Failed: {failed_docs}
- ⏭️ Skipped: {len(files_to_document) - successful_docs - failed_docs}

## Generated Documentation Files

"""
                for i, doc in enumerate(documentations, 1):
                    if doc.get("status") == "success" and doc.get("markdown_file"):
                        index_content += f"{i}. **{doc['file_name']}** - [{doc['markdown_filename']}]({doc['markdown_filename']})\n"
                        index_content += f"   - Type: {doc['file_extension']}\n"
                        index_content += f"   - Size: {doc['file_size']} bytes\n\n"
                
                # Save index file
                index_path = docs_output_dir / "README.md"
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(index_content)
                generated_files.append(str(index_path))
            
            # Extract download ID for the download endpoint
            download_id = extract_download_id_from_path(str(docs_output_dir)) if save_as_files else None
            
            # Prepare individual file metadata for frontend downloads
            individual_files = []
            if save_as_files:
                for doc in documentations:
                    if doc.get("status") == "success" and doc.get("markdown_file"):
                        individual_files.append({
                            "filename": doc["markdown_filename"],
                            "original_file": doc["file_name"],
                            "file_extension": doc["file_extension"],
                            "file_size": doc.get("file_size", 0)
                        })
            
            return {
                "status": "success",
                "message": f"Documentation generated for {len(files_to_document)} files",
                "files_processed": len(files_to_document),
                "successful_documentations": successful_docs,
                "failed_documentations": failed_docs,
                "skipped_files": len(files_to_document) - successful_docs - failed_docs,
                "supported_extensions": supported_extensions,
                "output_directory": str(docs_output_dir) if save_as_files else None,
                "generated_files": generated_files if save_as_files else [],
                "individual_files": individual_files,
                "download_id": download_id,
                "documentations": documentations
            }
            
    except zipfile.BadZipFile:
        return {
            "status": "error",
            "message": "Invalid ZIP file",
            "files_processed": 0,
            "documentations": []
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing ZIP file: {str(e)}",
            "files_processed": 0,
            "documentations": []
        }


def create_documentation_zip(output_dir: Path) -> Path:
    """Package documentation directory into a ZIP file
    
    Args:
        output_dir: Path to the documentation directory to package
        
    Returns:
        Path to the created ZIP file
        
    Raises:
        FileNotFoundError: If output directory doesn't exist
        Exception: If ZIP creation fails
    """
    try:
        if not output_dir.exists():
            raise FileNotFoundError(f"Documentation directory not found: {output_dir}")
        
        # Create ZIP filename based on directory name
        zip_filename = f"{output_dir.name}.zip"
        zip_path = output_dir.parent / zip_filename
        
        # Create ZIP file with all documentation files
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    # Calculate relative path for ZIP structure
                    arcname = file_path.relative_to(output_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path
        
    except Exception as e:
        raise Exception(f"Failed to create documentation ZIP: {str(e)}")


def extract_download_id_from_path(output_directory: str) -> str:
    """Extract download ID (timestamp) from documentation output directory path
    
    Args:
        output_directory: Full path to documentation directory
        
    Returns:
        Download ID (timestamp portion) for use in download endpoint
    """
    try:
        # Extract the directory name from the full path
        dir_name = Path(output_directory).name
        # For standard docs: docs_TIMESTAMP -> TIMESTAMP
        if dir_name.startswith("docs_"):
            return dir_name[5:]  # Remove "docs_" prefix
        
        # For RAG docs: rag_docs_TIMESTAMP -> TIMESTAMP  
        elif dir_name.startswith("rag_docs_"):
            return dir_name[9:]  # Remove "rag_docs_" prefix
        
        # Fallback: use the full directory name
        return dir_name
        
    except Exception:
        # Fallback: use current timestamp
        return datetime.now().strftime("%Y%m%d_%H%M%S")
