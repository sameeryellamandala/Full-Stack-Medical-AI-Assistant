"""Debug the chat pipeline directly to see the actual error."""
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.messages import HumanMessage, SystemMessage

print("Step 1: Creating embeddings...")
try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    print("  OK")
except Exception as e:
    print(f"  FAILED: {e}")
    exit(1)

print("Step 2: Connecting to Pinecone...")
try:
    vectorstore = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        embedding=embeddings
    )
    print("  OK")
except Exception as e:
    print(f"  FAILED: {e}")
    exit(1)

print("Step 3: Similarity search...")
try:
    docs = vectorstore.similarity_search("What is this report about?", k=3)
    print(f"  OK - Found {len(docs)} docs")
    for i, d in enumerate(docs):
        print(f"  Doc {i}: {d.page_content[:80]}...")
except Exception as e:
    print(f"  FAILED: {e}")
    exit(1)

print("Step 4: Calling Gemini LLM...")
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.1
    )
    context = "\n".join([doc.page_content for doc in docs])
    messages = [
        SystemMessage(content="You are a professional Medical AI Assistant. Be concise and helpful."),
        HumanMessage(content="What is this report about?"),
        SystemMessage(content=f"Context from files: {context}")
    ]
    response = llm.invoke(messages)
    print(f"  OK - Response: {response.content[:100]}...")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\nAll steps passed! The pipeline works.")
