import os
from dotenv import load_dotenv
from google import genai

# 1. Load environment variables from .env file
load_dotenv()

# 2. Get your Gemini API key from env vars
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# 3. Configure the Gemini client (it reads the API key automatically)
client = genai.Client()  # uses GEMINI_API_KEY from environment

# 4. Call embedding API
text_to_embed = "Hello, this is a test for embedding"
response = client.models.embed_content(
    model="gemini-embedding-001",  # embedding model name
    contents=text_to_embed
)

# 5. Print result
print(response.embeddings)
