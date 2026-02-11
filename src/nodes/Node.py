from langchain_core.documents import Document
from src.states.state import GraphState

from pydantic import BaseModel,Field
from langchain_core.prompts import ChatPromptTemplate
from src.llms.llm import Groqllm
from src.route.reposnse import rag_chain
from src.route.websearch import web_search_tool
from src.route.rewriteprompt import question_rewriter
from langchain_core.output_parsers import StrOutputParser



def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]

    # Lazy-load the vectorstore retriever to avoid heavy imports at module import time
    from src.rags.rag import get_vectorstore

    _, retriever = get_vectorstore(force_recreate=False)

    # Retrieval
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}

def generate(state):
    """
    Generate an answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains the LLM generation
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    # Generation
    generation = rag_chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}

def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]

    # Lazy import to avoid heavy dependencies at module import time
    from src.route.Grade import retrieval_grader

    # Score each doc
    filtered_docs = []
    for d in documents:
        score = retrieval_grader.invoke(
            {"question": question, "document": d.page_content}
        )
        grade = score.binary_score
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            continue
    return {"documents": filtered_docs, "question": question}


def transform_query(state):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """

    print("---TRANSFORM QUERY---")
    question = state["question"]
    documents = state["documents"]

    # Re-write question
    better_question = question_rewriter.invoke({"question": question})
    return {"documents": documents, "question": better_question}

def web_search(state):
    """
    Web search based on the re-phrased question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with appended web results
    """

    print("---WEB SEARCH---")
    question = state["question"]

    # Web search
    # The Tavily tool may accept a raw string or a dict; call with the string.
    docs = web_search_tool.invoke(question)

    # Normalize different possible return types into a list of Documents
    if isinstance(docs, str):
        web_results = Document(page_content=docs)
        documents = [web_results]
    elif isinstance(docs, list):
        # List of dicts with 'content'
        if all(isinstance(d, dict) and "content" in d for d in docs):
            web_text = "\n".join(d["content"] for d in docs)
            documents = [Document(page_content=web_text)]
        # List of Document-like objects
        elif all(hasattr(d, "page_content") for d in docs):
            documents = docs
        else:
            documents = [Document(page_content="\n".join(map(str, docs)))]
    elif hasattr(docs, "page_content"):
        documents = [docs]
    else:
        documents = [Document(page_content=str(docs))]

    return {"documents": documents, "question": question}
