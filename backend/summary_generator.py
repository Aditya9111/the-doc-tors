"""
Smart Summary Generator for RAG Optimization
Generates and caches intelligent summaries for code files using LLM
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from .utils.openai_utils import get_chat_llm


class SummaryCache:
    """Cache file summaries based on content hash to avoid regeneration"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / "summary_cache.json"
        self.cache = self._load_cache()
    
    def get(self, content_hash: str) -> Optional[str]:
        """Get cached summary by content hash"""
        return self.cache.get(content_hash)
    
    def set(self, content_hash: str, summary: str):
        """Cache a summary"""
        self.cache[content_hash] = summary
        self._save_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text())
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            self.cache_file.write_text(json.dumps(self.cache, indent=2))
        except Exception as e:
            print(f"Warning: Could not save summary cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "total_entries": len(self.cache),
            "cache_file_size": self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }


class SmartSummaryGenerator:
    """Generate intelligent summaries for code files using LLM with caching"""
    
    def __init__(self, cache_dir: Path):
        self.cache = SummaryCache(cache_dir)
        self.llm = get_chat_llm(model="gpt-4o-mini", temperature=0)
    
    def generate_python_summary(self, file_path: str, content: str, 
                                ast_chunks: List[Dict]) -> str:
        """Generate markdown summary for Python file"""
        
        # Check cache first
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        cached = self.cache.get(content_hash)
        if cached:
            return cached
        
        # Extract metadata from AST chunks
        functions = [c.get("name", "") for c in ast_chunks 
                    if c.get("type") == "function" and c.get("name")]
        classes = [c.get("name", "") for c in ast_chunks 
                  if c.get("type") == "class" and c.get("name")]
        imports = [c.get("content", "") for c in ast_chunks 
                  if c.get("type") == "import" and c.get("content")]
        
        # Build context for LLM
        context = f"""
File: {file_path}

Functions: {", ".join(functions[:10])}  # Limit to first 10
Classes: {", ".join(classes[:10])}
Imports: {", ".join(imports[:5])}

First 1500 characters:
{content[:1500]}
"""
        
        prompt = f"""Generate a concise markdown summary (3-4 sentences) for this Python file.

{context}

Include:
1. Primary purpose of the file
2. Key components (main functions/classes)
3. Main dependencies/technologies used
4. How it fits in the codebase (if obvious)

Format as markdown with file path as heading.
"""
        
        try:
            response = self.llm.invoke(prompt)
            summary = response.content.strip()
            
            # Validate summary quality
            if len(summary) < 50 or len(summary) > 1000:
                raise ValueError("Summary length out of expected range")
            
            # Cache the summary
            self.cache.set(content_hash, summary)
            return summary
            
        except Exception as e:
            print(f"Warning: LLM summary generation failed for {file_path}: {e}")
            # Fallback: generate simple summary from metadata
            return self._generate_fallback_summary(
                file_path, functions, classes, imports
            )
    
    def _generate_fallback_summary(self, file_path: str, 
                                   functions: List[str], classes: List[str], 
                                   imports: List[str]) -> str:
        """Generate basic summary without LLM as fallback"""
        summary = f"# {file_path}\n\n"
        
        if classes:
            summary += f"**Classes**: {', '.join(classes[:5])}\n\n"
        
        if functions:
            summary += f"**Functions**: {', '.join(functions[:10])}\n\n"
        
        if imports:
            # Extract module names from imports
            module_names = []
            for imp in imports[:5]:
                if "from" in imp:
                    module = imp.split("from")[1].split("import")[0].strip()
                    module_names.append(module)
                elif "import" in imp:
                    module = imp.split("import")[1].strip().split(",")[0].strip()
                    module_names.append(module)
            
            if module_names:
                summary += f"**Dependencies**: {', '.join(module_names)}\n"
        
        return summary
    
    def get_generation_stats(self) -> Dict:
        """Get statistics about summary generation"""
        cache_stats = self.cache.get_cache_stats()
        return {
            "cache_entries": cache_stats["total_entries"],
            "cache_size_bytes": cache_stats["cache_file_size"]
        }

