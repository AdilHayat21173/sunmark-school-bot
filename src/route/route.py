# Making a router that can route to chat, web search, or vectorstore retriever
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.llms.llm import Groqllm
#router prompt
from src.prompts.routerprompt import system



# Data model
class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["vectorstore", "web_search", "chat"] = Field(
        ...,
        description="Given a user question choose to route it to web search, vectorstore, or chat.",
    )

# llm from llms folder 
    
llm=Groqllm().get_llm()

structured_llm_router = llm.with_structured_output(RouteQuery)
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

question_router = route_prompt | structured_llm_router

