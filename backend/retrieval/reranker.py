from typing import List
from langchain_core.documents import Document

def rerank_documents(query: str, documents: List[Document], top_n: int = 5) -> List[Document]:
    """
    Reranks documents based on their relevance to the query.
    For now, this is a simple pass-through that returns the top_n documents.
    In a production setting, you would use a CrossEncoder or Cohere Rerank API here.
    """
    print(f"  Reranking {len(documents)} documents to top {top_n}")
    # Currently just returning the first top_n, assuming hybrid search already returned them in somewhat sorted order.
    # To implement true reranking, you could use sentence-transformers/cross-encoder/ms-marco-MiniLM-L-6-v2
    return documents[:top_n]
