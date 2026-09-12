from langchain_core.messages import SystemMessage, HumanMessage
import re

def _strip_thinking(text: str) -> str:
    """Strip <think>...</think> reasoning tokens from model output."""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    cleaned = re.sub(r'<think>.*$', '', cleaned, flags=re.DOTALL).strip()
    return cleaned if cleaned else text

def rewrite_query(llm, query: str, chat_history: list) -> str:
    """
    Rewrites the user query to be fully contextualized based on chat history.
    """
    if not chat_history:
        return query
        
    system_prompt = """You are an expert at query rewriting.
    Given a chat history and the latest user query, rewrite the user query to be a standalone question that can be understood without the chat history.
    Do not answer the question, just rewrite it.
    If it's already standalone, return it as is."""
    
    # Simple formatting of chat history
    history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in chat_history[-4:]])
    
    prompt = f"Chat History:\n{history_str}\n\nLatest Query: {query}\n\nStandalone Query:"
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=prompt)])
        return _strip_thinking(response.content.strip())
    except Exception as e:
        print(f"Query rewriting failed: {e}")
        return query

