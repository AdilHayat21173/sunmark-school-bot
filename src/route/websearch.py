import os
from dotenv import load_dotenv
from langchain_tavily import TavilySearch

load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("Error: TAVILY_API_KEY not found in .env file")

web_search_tool = TavilySearch(k=1)
