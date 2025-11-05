"""
Efficient Documentation Processor
Handles large file documentation with intelligent chunking, caching, and parallel processing
"""

import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from queue import Queue
from threading import Thread, Lock
from functools import wraps

from .token_manager import TokenManager
from .utils.openai_utils import get_chat_llm
from .chunking import chunk_file


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise  # Last attempt, re-raise error
                    
                    # Exponential backoff: 1s, 2s, 4s
                    delay = base_delay * (2 ** attempt)
                    print(f"Retry {attempt + 1}/{max_retries} after {delay}s: {str(e)}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


class DocumentationCache:
    """Simple in-memory cache for documentation with TTL"""
    
    def __init__(self, ttl_hours: int = 24):
        self.cache = {}
        self.ttl = timedelta(hours=ttl_hours)
    
    def get(self, content: str) -> Optional[str]:
        """Get cached documentation by content hash"""
        file_hash = hashlib.md5(content.encode()).hexdigest()
        
        if file_hash in self.cache:
            cached_data, timestamp = self.cache[file_hash]
            if datetime.now() - timestamp < self.ttl:
                return cached_data
            else:
                del self.cache[file_hash]  # Expired
        
        return None
    
    def set(self, content: str, documentation: str):
        """Cache documentation with timestamp"""
        file_hash = hashlib.md5(content.encode()).hexdigest()
        self.cache[file_hash] = (documentation, datetime.now())
    
    def clear_expired(self):
        """Remove expired entries"""
        now = datetime.now()
        expired = [k for k, (_, ts) in self.cache.items() if now - ts > self.ttl]
        for k in expired:
            del self.cache[k]


class SimpleParallelProcessor:
    """Simple parallel processor with max 3 workers"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
    
    def process_files(self, files: List[Dict], process_func) -> List[Dict]:
        """Process files with simple threading"""
        if len(files) <= 1:
            # Single file - no need for threading
            return [process_func(files[0])]
        
        results = []
        result_lock = Lock()
        
        def worker(file_queue):
            while True:
                try:
                    file_data = file_queue.get(timeout=1)
                    if file_data is None:
                        break
                    
                    result = process_func(file_data)
                    
                    with result_lock:
                        results.append(result)
                    
                    file_queue.task_done()
                except:
                    break
        
        # Create queue and add files
        queue = Queue()
        for file in files:
            queue.put(file)
        
        # Start workers (max 3)
        workers = []
        num_workers = min(self.max_workers, len(files))
        for _ in range(num_workers):
            t = Thread(target=worker, args=(queue,))
            t.start()
            workers.append(t)
        
        # Wait for completion
        queue.join()
        
        # Stop workers
        for _ in range(num_workers):
            queue.put(None)
        for t in workers:
            t.join()
        
        return results


class DocumentationProcessor:
    """Main documentation processor with intelligent chunking and caching"""
    
    def __init__(self, mode: str = "standard"):
        self.mode = mode
        self.token_manager = TokenManager()
        self.cache = DocumentationCache()
        self.parallel_processor = SimpleParallelProcessor(max_workers=3)
    
    def process_file(self, file_path: str, content: str) -> Dict:
        """Process single file with caching and retry"""
        start_time = time.time()
        
        # 1. Check cache
        if cached := self.cache.get(content):
            return {
                "status": "success",
                "file_name": file_path,
                "documentation": cached,
                "cached": True,
                "processing_time": 0,
                "strategy": "cached"
            }
        
        # 2. Estimate tokens and select strategy
        tokens = self.token_manager.estimate_tokens(content)
        strategy = self.select_strategy(tokens)
        
        # 3. Process based on strategy
        try:
            if strategy == "full":
                doc = self.process_full_file(content, file_path)
            elif strategy == "chunked":
                doc = self.process_chunked(content, file_path)
            elif strategy == "summarized":
                doc = self.process_summarized(content, file_path)
            else:  # structure_only
                doc = self.process_structure_only(content, file_path)
            
            # 4. Cache result
            self.cache.set(content, doc)
            
            return {
                "status": "success",
                "file_name": file_path,
                "documentation": doc,
                "strategy": strategy,
                "tokens": tokens,
                "processing_time": time.time() - start_time,
                "cached": False
            }
        
        except Exception as e:
            return {
                "status": "error",
                "file_name": file_path,
                "error": str(e),
                "strategy": strategy,
                "processing_time": time.time() - start_time
            }
    
    def select_strategy(self, tokens: int) -> str:
        """Select processing strategy based on token count"""
        if tokens < 4000:
            return "full"
        elif tokens < 20000:
            return "chunked"
        elif tokens < 100000:
            return "summarized"
        else:
            return "structure_only"
    
    @retry_with_backoff(max_retries=3)
    def process_full_file(self, content: str, file_path: str) -> str:
        """Process entire file in one LLM call"""
        llm = get_chat_llm(model="gpt-4o-mini", temperature=0.1)
        prompt = self.create_prompt(content, file_path)
        return llm.invoke(prompt).content
    
    def process_chunked(self, content: str, file_path: str) -> str:
        """Process file in chunks and merge"""
        file_ext = Path(file_path).suffix
        chunks = self.chunk_for_documentation(content, file_ext, max_tokens=4000)
        
        # Document each chunk
        chunk_docs = []
        for i, chunk in enumerate(chunks):
            doc = self.document_chunk(chunk, file_path, i, len(chunks))
            chunk_docs.append(doc)
        
        # Merge documentation
        return self.merge_chunk_docs(chunk_docs, file_path)
    
    def process_summarized(self, content: str, file_path: str) -> str:
        """Process large file with summarization"""
        # Extract key sections (first 50% and last 20%)
        lines = content.split('\n')
        total_lines = len(lines)
        
        # Take first 50% and last 20%
        first_part = lines[:total_lines // 2]
        last_part = lines[int(total_lines * 0.8):]
        
        # Combine key sections
        key_content = '\n'.join(first_part + ['\n... (middle section omitted) ...\n'] + last_part)
        
        # Truncate to fit in context
        if not self.token_manager.fits_in_context(key_content, 4000):
            key_content = self.token_manager.truncate_to_tokens(key_content, 4000)
        
        return self.process_full_file(key_content, file_path)
    
    def process_structure_only(self, content: str, file_path: str) -> str:
        """Process very large file - structure only"""
        file_ext = Path(file_path).suffix
        
        # Extract structure based on file type
        if file_ext.lower() == '.py':
            structure = self.extract_python_structure(content)
        elif file_ext.lower() in ['.js', '.jsx', '.ts', '.tsx']:
            structure = self.extract_javascript_structure(content)
        else:
            # Generic structure extraction
            lines = content.split('\n')
            structure = f"File: {file_path}\n"
            structure += f"Total lines: {len(lines)}\n"
            structure += f"File size: {len(content)} characters\n"
            structure += "Content too large for detailed analysis.\n"
            return structure
        
        return self.process_full_file(structure, file_path)
    
    def chunk_for_documentation(self, content: str, file_ext: str, max_tokens: int = 4000) -> List[str]:
        """Chunk content for documentation processing"""
        # Use existing chunking logic
        chunks = chunk_file(content, file_ext)
        
        # Combine small chunks to fit token limit
        combined_chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for chunk in chunks:
            tokens = self.token_manager.estimate_tokens(chunk)
            if current_tokens + tokens < max_tokens:
                current_chunk += "\n\n" + chunk
                current_tokens += tokens
            else:
                if current_chunk:
                    combined_chunks.append(current_chunk)
                current_chunk = chunk
                current_tokens = tokens
        
        if current_chunk:
            combined_chunks.append(current_chunk)
        
        return combined_chunks
    
    def document_chunk(self, chunk: str, file_path: str, chunk_index: int, total_chunks: int) -> str:
        """Document a single chunk"""
        llm = get_chat_llm(model="gpt-4o-mini", temperature=0.1)
        
        prompt = f"""
        Analyze this code chunk and generate documentation:
        
        File: {file_path}
        Chunk {chunk_index + 1} of {total_chunks}
        
        Code:
        ```python
        {chunk}
        ```
        
        Please provide:
        1. **Overview**: What this chunk does
        2. **Functions/Classes**: List any functions or classes
        3. **Key Logic**: Important implementation details
        4. **Dependencies**: What this chunk depends on
        
        Keep it concise and focused on this specific chunk.
        """
        
        return llm.invoke(prompt).content
    
    def merge_chunk_docs(self, chunk_docs: List[str], file_path: str) -> str:
        """Merge documentation from multiple chunks"""
        merged = f"# {Path(file_path).name} Documentation\n\n"
        merged += f"*Generated from {len(chunk_docs)} chunks*\n\n"
        
        for i, doc in enumerate(chunk_docs):
            merged += f"## Section {i + 1}\n\n"
            merged += doc + "\n\n"
        
        return merged
    
    def extract_python_structure(self, content: str) -> str:
        """Extract Python file structure"""
        lines = content.split('\n')
        structure = f"# {Path(content).name} Structure\n\n"
        
        # Find classes and functions
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('class '):
                structure += f"**Class**: {stripped}\n"
            elif stripped.startswith('def ') and not stripped.startswith('def _'):
                structure += f"**Function**: {stripped}\n"
            elif stripped.startswith('import ') or stripped.startswith('from '):
                structure += f"**Import**: {stripped}\n"
        
        return structure
    
    def extract_javascript_structure(self, content: str) -> str:
        """Extract JavaScript file structure"""
        lines = content.split('\n')
        structure = f"# {Path(content).name} Structure\n\n"
        
        # Find functions, classes, and exports
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('function ') or stripped.startswith('const ') and '=' in stripped:
                structure += f"**Function**: {stripped}\n"
            elif stripped.startswith('class '):
                structure += f"**Class**: {stripped}\n"
            elif stripped.startswith('export '):
                structure += f"**Export**: {stripped}\n"
        
        return structure
    
    def create_prompt(self, content: str, file_path: str) -> str:
        """Create documentation prompt based on file type"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.py':
            return f"""
            Analyze this Python file and generate comprehensive documentation:
            
            File: {file_path}
            
            Code:
            ```python
            {content}
            ```
            
            Please provide:
            1. **File Overview**: Brief description of what this file does
            2. **Functions**: List all functions with descriptions, parameters, and return values
            3. **Classes**: List all classes with descriptions and their methods
            4. **Imports**: Explain what external dependencies this file uses
            5. **Key Features**: Main functionality and purpose
            6. **Usage Examples**: How to use the main functions/classes
            7. **Dependencies**: What other files this might depend on
            
            Format the response as structured markdown.
            """
        elif file_ext in ['.js', '.jsx', '.ts', '.tsx']:
            return f"""
            Analyze this JavaScript/TypeScript file and generate comprehensive documentation:
            
            File: {file_path}
            
            Code:
            ```javascript
            {content}
            ```
            
            Please provide:
            1. **File Overview**: Brief description of what this file does
            2. **Functions**: List all functions with descriptions, parameters, and return values
            3. **Classes/Components**: List all classes or React components with descriptions
            4. **Exports**: What this file exports and how to import it
            5. **Key Features**: Main functionality and purpose
            6. **Usage Examples**: How to use the main functions/components
            7. **Dependencies**: What external libraries or files this depends on
            
            Format the response as structured markdown.
            """
        else:
            return f"""
            Analyze this file and generate documentation:
            
            File: {file_path}
            
            Content:
            ```
            {content}
            ```
            
            Please provide:
            1. **File Overview**: Brief description of what this file contains
            2. **Main Purpose**: What this file is used for
            3. **Key Information**: Important details or instructions
            4. **Structure**: How the content is organized
            
            Format the response as structured markdown.
            """
    
    def process_multiple_files(self, files: List[Dict]) -> List[Dict]:
        """Process multiple files with simple parallel processing"""
        if len(files) <= 1:
            return [self.process_file(f['path'], f['content']) for f in files]
        
        return self.parallel_processor.process_files(
            files,
            lambda f: self.process_file(f['path'], f['content'])
        )
