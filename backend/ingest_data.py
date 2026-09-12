import os
from langchain_community.document_loaders import PyMuPDFLoader  # Better loader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

load_dotenv()

def ingest_pdf(file_path, user_id, document_id=""):
    # Extract just the filename (e.g., "svethka.pdf") for metadata tagging
    filename = os.path.basename(file_path)
    print(f"--- Starting Ingestion for {filename} (User: {user_id}) ---")
    
    # 1. Load using PyMuPDF (much more reliable)
    loader = PyMuPDFLoader(file_path)
    data = loader.load()
    print(f"  Loaded {len(data)} pages from PDF")
    
    # 2. Split into chunks (improved chunking strategy)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # Smaller chunks for more precise retrieval
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    docs = text_splitter.split_documents(data)
    print(f"  Split into {len(docs)} chunks")
    
    # 3. Tag every chunk with metadata
    import uuid
    for i, doc in enumerate(docs):
        doc.metadata["source_filename"] = filename
        doc.metadata["user_id"] = user_id
        doc.metadata["document_id"] = document_id or str(uuid.uuid4())
        doc.metadata["chunk_id"] = f"{doc.metadata['document_id']}_chunk_{i}"
        # PyMuPDF naturally stores 'page' in doc.metadata, but we ensure it's explicitly there
        if "page" not in doc.metadata:
            doc.metadata["page"] = 0
        
        # Placeholder for extraction/detection logic
        doc.metadata["section"] = "general"
        doc.metadata["document_type"] = "medical_report"
        doc.metadata["medical_date"] = "unknown"
        
    print(f"  Tagged all chunks with rich metadata")
    
    # 4. Create Embeddings - using HuggingFace Local Embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # 5. Upload to Pinecone (Vector Search)
    index_name = os.getenv("PINECONE_INDEX_NAME")
    PineconeVectorStore.from_documents(docs, embeddings, index_name=index_name)
    
    # 6. Update Local BM25 Retriever (Keyword Search)
    import pickle
    from langchain_community.retrievers import BM25Retriever
    bm25_path = "bm25_retriever.pkl"
    all_docs = docs
    if os.path.exists(bm25_path):
        with open(bm25_path, "rb") as f:
            existing_retriever = pickle.load(f)
            all_docs = existing_retriever.docs + docs
    
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    with open(bm25_path, "wb") as f:
        pickle.dump(bm25_retriever, f)
        
    print(f"--- Success! {len(docs)} chunks uploaded to Pinecone and BM25 index updated ---")
    
    # 6. Return details for the frontend
    chunk_previews = []
    for i, doc in enumerate(docs[:5]):  # Show first 5 chunks as preview
        chunk_previews.append({
            "chunk_number": i + 1,
            "preview": doc.page_content[:120] + "..." if len(doc.page_content) > 120 else doc.page_content,
            "char_count": len(doc.page_content)
        })
    
    return {
        "total_pages": len(data),
        "total_chunks": len(docs),
        "chunk_previews": chunk_previews
    }

if __name__ == "__main__":
    if os.path.exists("report.pdf"):
        ingest_pdf("report.pdf", user_id="test_user")
    else:
        print("Error: report.pdf not found in the backend folder!")