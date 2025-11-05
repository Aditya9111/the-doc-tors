from typing import Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from ..config import OPENAI_API_KEY, OPENAI_TIMEOUT


class OpenAIError(Exception):
    pass


def get_embeddings(model: str = "text-embedding-3-small") -> OpenAIEmbeddings:
    if not OPENAI_API_KEY:
        raise OpenAIError("OPENAI_API_KEY not found in environment variables")
    
    return OpenAIEmbeddings(
        model=model, 
        api_key=OPENAI_API_KEY,
        request_timeout=OPENAI_TIMEOUT
    )


def get_chat_llm(
    model: str = "gpt-4o-mini", 
    temperature: float = 0.0,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None
) -> ChatOpenAI:
    if not OPENAI_API_KEY:
        raise OpenAIError("OPENAI_API_KEY not found in environment variables")
    
    return ChatOpenAI(
        model=model, 
        temperature=temperature,
        api_key=OPENAI_API_KEY,
        request_timeout=timeout or OPENAI_TIMEOUT,
        max_tokens=max_tokens
    )
