import os
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from dotenv import load_dotenv

load_dotenv()

models_to_test = [
    "nvidia/nemotron-3-embed-1b-nvfp4",
    "nemotron-3-embed-1b-nvfp4",
    "nvidia/nv-embedqa-e5-v5",
    "NV-Embed-QA",
    "nvidia/nv-embed-v1"
]

for model in models_to_test:
    print(f"Testing model: {model}")
    try:
        embeddings = NVIDIAEmbeddings(model=model, api_key=os.getenv("NVIDIA_API_KEY"))
        result = embeddings.embed_query("This is a test.")
        print(f"  Success! Dimension: {len(result)}")
        break # Stop on first success
    except Exception as e:
        print(f"  Failed: {e}")
