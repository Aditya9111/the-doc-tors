# app/chunking.py
import ast
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Base splitter for fallback
base_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    length_function=len,
)

def chunk_text_file(content: str):
    # Split plain text / markdown respecting headings.
    sections = re.split(r'(?=^#{1,6} )', content, flags=re.M)
    final_chunks = []
    for sec in sections:
        if len(sec) > 1000:
            final_chunks.extend(base_splitter.split_text(sec))
        else:
            final_chunks.append(sec)
    return final_chunks


def chunk_python_file(content: str):
    # Advanced Python chunking using AST with fallbacks.
    chunks = []
    try:
        tree = ast.parse(content)
        lines = content.splitlines()

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                block = "\n".join(lines[node.lineno - 1: node.end_lineno])
                chunks.append({ "type": "import", "content": block })

            elif isinstance(node, ast.FunctionDef):
                block = "\n".join(lines[node.lineno - 1: node.end_lineno])
                doc = ast.get_docstring(node)
                chunks.append({
                    "type": "function",
                    "name": node.name,
                    "docstring": doc,
                    "content": block
                })

            elif isinstance(node, ast.ClassDef):
                block = "\n".join(lines[node.lineno - 1: node.end_lineno])
                chunks.append({
                    "type": "class",
                    "name": node.name,
                    "content": block
                })

    except Exception:
        raw_chunks = re.split(r'(?=^def |^class )', content, flags=re.M)
        chunks = [{ "type": "raw", "content": ch } for ch in raw_chunks]

    final_chunks = []
    for ch in chunks:
        content = ch["content"] if isinstance(ch, dict) else ch
        if len(content) > 1000:
            for sub in base_splitter.split_text(content):
                final_chunks.append({**ch, "content": sub})
        else:
            final_chunks.append(ch)

    return final_chunks


def chunk_javascript_file(content: str):
    # Split JS into functions, classes, and blocks.
    chunks = []
    parts = re.split(r'(?=function |class |=>)', content)

    for part in parts:
        if "function" in part:
            chunks.append({ "type": "function", "content": part })
        elif "class" in part:
            chunks.append({ "type": "class", "content": part })
        else:
            chunks.append({ "type": "block", "content": part })

    final_chunks = []
    for ch in chunks:
        if len(ch["content"]) > 1000:
            for sub in base_splitter.split_text(ch["content"]):
                final_chunks.append({**ch, "content": sub})
        else:
            final_chunks.append(ch)

    return final_chunks


def create_enhanced_python_chunks(content: str, file_path: str, 
                                  summary_generator) -> list:
    # 
    # Create multi-tier chunks for Python files:
    # - Tier 1: File summary (fast search)
    # - Tier 2: Function/class chunks (detailed answers)
    # - Tier 3: Full source reference (metadata only)
    # 
    chunks = []
    
    # Get standard AST chunks
    ast_chunks = chunk_python_file(content)
    
    # TIER 1: Generate and store file summary
    try:
        summary = summary_generator.generate_python_summary(
            file_path, content, ast_chunks
        )
        chunks.append({
            "type": "summary",
            "content": summary,
            "tier": 1,
            "file_path": file_path,
            "search_priority": "high"
        })
    except Exception as e:
        print(f"Warning: Could not generate summary for {file_path}: {e}")
    
    # TIER 2: Enhanced AST chunks with signatures
    for chunk in ast_chunks:
        if chunk.get("type") in ["function", "class"]:
            # Create searchable representation
            searchable_content = chunk.get("content", "")
            
            # Add signature/docstring for better search
            if chunk.get("docstring"):
                searchable_content = (
                    f"## {chunk.get('name', 'Unknown')}\n\n"
                    f"**File**: {file_path}\n\n"
                    f"**Documentation**: {chunk['docstring']}\n\n"
                    f"```python\n{searchable_content}\n```"
                )
            else:
                # Still add file context even without docstring
                searchable_content = (
                    f"## {chunk.get('name', 'Unknown')}\n\n"
                    f"**File**: {file_path}\n\n"
                    f"```python\n{searchable_content}\n```"
                )
            
            chunks.append({
                "type": chunk.get("type"),
                "name": chunk.get("name"),
                "content": searchable_content,
                "tier": 2,
                "file_path": file_path
            })
        else:
            # Imports and other chunks
            chunks.append({
                **chunk,
                "tier": 2,
                "file_path": file_path
            })
    
    return chunks


def chunk_file(content: str, file_extension: str, file_path: str = None, 
               summary_generator=None):
    # # Enhanced chunking with optional summary generation
    ext = file_extension.lower()
    
    if ext == ".py" and summary_generator and file_path:
        return create_enhanced_python_chunks(
            content, file_path, summary_generator
        )
    elif ext in [".txt", ".md", ".log"]:
        return chunk_text_file(content)
    elif ext == ".py":
        return chunk_python_file(content)
    elif ext in [".js", ".jsx"]:
        return chunk_javascript_file(content)
    else:
        return base_splitter.split_text(content)
