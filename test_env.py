import os
from dotenv import load_dotenv

load_dotenv()

print("=== API KEY TEST ===")
print(f"NEWS_API_KEY: {os.getenv('NEWS_API_KEY', 'MISSING')[:20]}...")
print(f"GROQ_API_KEY: {os.getenv('GROQ_API_KEY', 'MISSING')[:20]}...")
print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY', 'MISSING')[:20]}...")
print(f"LLM_BACKEND: {os.getenv('LLM_BACKEND', 'NOT SET')}")
