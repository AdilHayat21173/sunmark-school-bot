## Grade documenr node
# Retriver document  
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from src.rags.rag import get_vectorstore
from src.llms.llm import Groqllm
from src.prompts.routerprompt import binary_system

class Grader(BaseModel):
    "binary classification of the document it give yes if relevant of document and no if not relevant"
    binary_score: str = Field(description="binary score of the document, yes or no")



llm = Groqllm().get_llm()

structured_llm_grader=llm.with_structured_output(Grader)



# Prompt

grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", binary_system),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
    ]
)

##chain the prompt with the LLM
retrieval_grader = grade_prompt | structured_llm_grader
question = "tell me about the sunmark school"
vectorstore, retriever = get_vectorstore(force_recreate=False)    
results = retriever.invoke(question)
docs = retriever.invoke(question)
doc_txt = docs[1].page_content
print(retrieval_grader.invoke({"question": question, "document": doc_txt}))
