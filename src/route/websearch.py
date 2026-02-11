import os
from dotenv import load_dotenv
# Use the correct import from langchain-tavily
from langchain_tavily import TavilySearch

# Load environment variables from .env file
load_dotenv()

# Verify API key is loaded
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("Error: TAVILY_API_KEY not found in .env file")

print(f"✓ Tavily API Key loaded: {tavily_api_key[:10]}...")


# Initialize the search tool
web_search_tool = TavilySearch(k=1)

