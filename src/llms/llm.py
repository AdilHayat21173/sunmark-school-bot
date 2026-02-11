import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

class Groqllm:
    def __init__(self):
        load_dotenv()   
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.llm = None
        
    def get_llm(self):
        """Initialize and return the LLM client"""
        try:
            if not self.groq_api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            
            os.environ["GROQ_API_KEY"] = self.groq_api_key
            self.llm = ChatGroq(api_key=self.groq_api_key, model="openai/gpt-oss-120b")
            return self.llm
        except Exception as e:
            raise ValueError(f"Error occurred with exception: {e}")
    
    def invoke(self, message):
        """Get a response from the LLM for the given message"""
        if not self.llm:
            self.get_llm()
        
        response = self.llm.invoke(message)
        return response.content