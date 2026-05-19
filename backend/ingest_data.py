import os
from langchain_community.document_loaders import PyMuPDFLoader  # Better loader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

load_dotenv()

def ingest_pdf(file_path):
    # Extract just the filename (e.g., "svethka.pdf") for metadata tagging
    filename = os.path.basename(file_path)
    print(f"--- Starting Ingestion for {filename} ---")
    
    # 1. Load using PyMuPDF (much more reliable)
    loader = PyMuPDFLoader(file_path)
    data = loader.load()
    print(f"  Loaded {len(data)} pages from PDF")
    
    # 2. Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    docs = text_splitter.split_documents(data)
    print(f"  Split into {len(docs)} chunks")
    
    # 3. Tag every chunk with source_filename so we can filter by document later
    for doc in docs:
        doc.metadata["source_filename"] = filename
    print(f"  Tagged all chunks with source_filename='{filename}'")
    
    # 4. Create Embeddings - using confirmed available model for this API key
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # 5. Upload to Pinecone
    index_name = os.getenv("PINECONE_INDEX_NAME")
    PineconeVectorStore.from_documents(docs, embeddings, index_name=index_name)
    
    print(f"--- Success! {len(docs)} chunks uploaded to Pinecone ---")
    
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
        ingest_pdf("report.pdf")
    else:
        print("Error: report.pdf not found in the backend folder!")