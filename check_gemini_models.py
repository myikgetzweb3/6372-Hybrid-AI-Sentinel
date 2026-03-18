import google.generativeai as genai
import os

# Get API key from .env (simplified for check)
def get_key():
    env_path = "/home/myikgetzweb3/6372-hybrid-ai-sentinel/.env"
    with open(env_path, "r") as f:
        for line in f:
            if line.strip().startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None

key = get_key()
if key:
    genai.configure(api_key=key)
    print("--- AVAILABLE MODELS ---")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Name: {m.name} | Display: {m.display_name}")
    except Exception as e:
        print(f"Error listing models: {e}")
else:
    print("API Key not found.")
