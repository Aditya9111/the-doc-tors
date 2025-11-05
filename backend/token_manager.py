"""
Token Management Module
Handles token estimation and management for documentation generation
"""

import tiktoken
from typing import Optional

class TokenManager:
    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize token manager with specified model"""
        self.model = model
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding if model not found
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        if not text:
            return text
        
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        # Truncate and decode back to text
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
    
    def fits_in_context(self, text: str, max_tokens: int = 4000) -> bool:
        """Check if text fits in context window"""
        return self.estimate_tokens(text) <= max_tokens
    
    def get_token_count_info(self, text: str) -> dict:
        """Get detailed token information"""
        tokens = self.encoding.encode(text)
        return {
            "token_count": len(tokens),
            "character_count": len(text),
            "tokens_per_character": len(tokens) / len(text) if text else 0,
            "model": self.model
        }
    
    def split_text_by_tokens(self, text: str, max_tokens: int) -> list:
        """Split text into chunks that fit within token limit"""
        if self.fits_in_context(text, max_tokens):
            return [text]
        
        tokens = self.encoding.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
        
        return chunks
