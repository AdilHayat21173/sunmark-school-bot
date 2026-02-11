## Generate a response
from src.llms.llm import Groqllm
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
"""RAG response chain setup.

This module defines `rag_chain` (prompt -> llm -> parser). Avoid invoking
the chain at import time; callers should call `rag_chain.invoke(...)` with
their own `context` and `question`.
"""

# Create your own RAG prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise."),
    ("human", "Question: {question}\n\nContext: {context}\n\nAnswer:")
])

llm = Groqllm().get_llm()

# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Chain
rag_chain = prompt | llm | StrOutputParser()