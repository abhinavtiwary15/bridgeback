import config
import os
print("OS DEFAULT_LLM:", os.getenv("DEFAULT_LLM"))
print("CONFIG DEFAULT_LLM:", config.DEFAULT_LLM)
print("GEMINI API KEY:", config.GEMINI_API_KEY)
