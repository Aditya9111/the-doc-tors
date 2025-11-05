from .utils.openai_utils import get_chat_llm, get_embeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from .config import VECTOR_DIR
from .version_manager import version_manager
import os


def build_qa_chain(vectorstore_path: str = None, version_metadata: dict = None):
    """Build the question-answering chain"""
    try:
        # Use provided vectorstore path or default
        persist_dir = vectorstore_path or str(VECTOR_DIR)
        
        # Check if vectorstore exists
        if not os.path.exists(persist_dir):
            raise FileNotFoundError(f"No vectorstore found at {persist_dir}. Please ingest documents first.")
        
        # Load vectorstore with embeddings
        embeddings = get_embeddings()
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
        
        # Check if vectorstore has documents
        if vectorstore._collection.count() == 0:
            raise ValueError("Vectorstore is empty. Please ingest documents first.")
        
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 4},
            search_type="similarity"
        )

        llm = get_chat_llm(model="gpt-4o-mini", temperature=0)

        # Build version context string
        version_context = ""
        if version_metadata:
            version_context = f"You are analyzing the '{version_metadata['version_name']}' version"
            if version_metadata.get('description'):
                version_context += f" ({version_metadata['description']})"
            version_context += ".\n"
        else:
            # Fallback when metadata not available (rare edge case)
            version_context = "You are analyzing the codebase.\n"

        template = f"""
        You are an intelligent assistant with access to project documentation and code.
        {version_context}Use the provided context to answer the question as accurately and helpfully as possible.
        
        Guidelines:
        - Base your answer primarily on the provided context
        - If the context doesn't contain enough information, say so clearly
        - Provide specific examples from the code when relevant
        - Be concise but comprehensive
        - If you're unsure about something, express that uncertainty

        Context:
        {{context}}

        Question:
        {{question}}

        Answer:
        """

        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=template,
        )

        qa = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True,
        )
        return qa
        
    except Exception as e:
        raise Exception(f"Error building QA chain: {str(e)}")


def answer_question(query: str, version_id: str = None):
    """Answer a question using the ingested documents"""
    try:
        # Determine which vectorstore to use
        vectorstore_path = None
        version_info = None
        
        if version_id:
            # Query specific version
            version = version_manager.get_version(version_id)
            if not version:
                raise ValueError(f"Version {version_id} not found")
            vectorstore_path = version.vectorstore_path
            version_info = {
                "version_id": version.version_id,
                "version_name": version.version_name,
                "description": version.description
            }
        else:
            # Use latest version or default vectorstore
            latest_version = version_manager.get_latest_version()
            if latest_version:
                vectorstore_path = latest_version.vectorstore_path
                version_info = {
                    "version_id": latest_version.version_id,
                    "version_name": latest_version.version_name,
                    "description": latest_version.description
                }
        
        qa = build_qa_chain(vectorstore_path, version_info)
        result = qa.invoke({"query": query})
        
        # Extract sources with additional metadata
        sources = []
        for doc in result["source_documents"]:
            source_info = {
                "file": doc.metadata.get("source", "Unknown"),
                "chunk_type": doc.metadata.get("chunk_type", "text"),
                "chunk_name": doc.metadata.get("chunk_name", ""),
                "file_extension": doc.metadata.get("file_extension", ""),
                "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            }
            sources.append(source_info)
        
        response = {
            "answer": result["result"],
            "sources": sources,
            "query": query
        }
        
        if version_info:
            response["version_info"] = version_info
        
        return response
        
    except Exception as e:
        raise Exception(f"Error answering question: {str(e)}")


def compare_versions(query: str, version_ids: list):
    """Compare answers across multiple versions"""
    try:
        results = []
        
        for version_id in version_ids:
            version = version_manager.get_version(version_id)
            if not version:
                continue
                
            try:
                answer = answer_question(query, version_id)
                results.append({
                    "version_id": version_id,
                    "version_name": version.version_name,
                    "description": version.description,
                    "answer": answer["answer"],
                    "sources_count": len(answer["sources"])
                })
            except Exception as e:
                results.append({
                    "version_id": version_id,
                    "version_name": version.version_name,
                    "description": version.description,
                    "error": str(e)
                })
        
        return {
            "query": query,
            "comparison_results": results,
            "total_versions": len(results)
        }
        
    except Exception as e:
        raise Exception(f"Error comparing versions: {str(e)}")
