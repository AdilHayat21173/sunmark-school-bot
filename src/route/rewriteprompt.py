# if the Answer Grader are return the no it use th ere writer to better making the question to give answer form vectorstore retriever
from pydantic import BaseModel,Field
from langchain_core.prompts import ChatPromptTemplate
from src.llms.llm import Groqllm
from src.route.Grade import docs,question
from src.route.reposnse import generation
from langchain_core.output_parsers import StrOutputParser

system = """You a question re-writer that converts an input question to a better version that is optimized \n 
     for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""


llm=Groqllm().get_llm()

re_write_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "Here is the initial question: \n\n {question} \n Formulate an improved question.",
        ),
    ]
)

question_rewriter = re_write_prompt | llm | StrOutputParser()
result = question_rewriter.invoke({"question": question})
print("Rewritten Question:", result)