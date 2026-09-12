import os
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from dotenv import load_dotenv

load_dotenv()

try:
    models = NVIDIAEmbeddings.get_available_models()
    embed_models = [m for m in models if m.model_type == "embedding"]
    print("Available Embedding Models:")
    for m in embed_models:
        print(m.id)
except Exception as e:
    print(f"Error listing models: {e}")
