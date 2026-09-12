import os
import pickle
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

def get_hybrid_retriever(user_id: str, active_document: str = ""):
    # 1. Setup Dense Retriever
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    vectorstore = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        embedding=embeddings
    )
    
    # Configure Pinecone retriever to filter by user_id and active_document
    filter_dict = {"user_id": user_id}
    if active_document:
        filter_dict["source_filename"] = active_document
        
    dense_retriever = vectorstore.as_retriever(
        search_kwargs={"k": 10, "filter": filter_dict}
    )
    
    # 2. Setup BM25 Retriever
    bm25_path = "bm25_retriever.pkl"
    bm25_retriever = None
    if os.path.exists(bm25_path):
        with open(bm25_path, "rb") as f:
            bm25_retriever = pickle.load(f)
            bm25_retriever.k = 10
            
    def hybrid_search(query: str):
        print(f"  Hybrid Search for: '{query}'")
        results = []
        
        # Get dense results
        dense_results = dense_retriever.invoke(query)
        print(f"  Found {len(dense_results)} dense results")
        results.extend(dense_results)
        
        # Get BM25 results and filter manually by user_id and active_document
        if bm25_retriever:
            all_bm25_results = bm25_retriever.invoke(query)
            filtered_bm25 = []
            for doc in all_bm25_results:
                if doc.metadata.get("user_id") == user_id:
                    if not active_document or doc.metadata.get("source_filename") == active_document:
                        filtered_bm25.append(doc)
            print(f"  Found {len(filtered_bm25)} filtered BM25 results")
            results.extend(filtered_bm25)
            
        # Deduplicate
        unique_results = []
        seen_chunks = set()
        for doc in results:
            chunk_id = doc.metadata.get("chunk_id")
            if chunk_id and chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_results.append(doc)
            elif not chunk_id:
                # Fallback deduplication if chunk_id is missing
                unique_results.append(doc)
                
        print(f"  Total unique hybrid results: {len(unique_results)}")
        return unique_results
        
    return hybrid_search
