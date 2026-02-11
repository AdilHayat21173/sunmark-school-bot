# Making a router it go to web search or  vectorstore retriever
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

from llms.llm import Groqllm
#router prompt
from prompts.routerprompt import system



# Data model
class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["vectorstore", "web_search"] = Field(
        ...,
        description="Given a user question choose to route it to web search or a vectorstore.",
    )

# llm from llms folder 
    
llm=Groqllm().get_llm()
structured_llm_question=llm.with_structured_output(RouteQuery)


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)
# LLM with function call

structured_llm_router = llm.with_structured_output(RouteQuery)
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

question_router = route_prompt | structured_llm_router

print(
    question_router.invoke(
        {"question": "Tell me about the sunmark school curriculum and subjects offered?"}
    )
)