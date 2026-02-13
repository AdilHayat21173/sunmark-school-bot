from langchain_core.documents import Document
from src.route.reposnse import rag_chain
from src.route.rewriteprompt import question_rewriter
from functools import lru_cache


@lru_cache(maxsize=1)
def get_chat_llm():
    from src.llms.llm import Groqllm
    return Groqllm().get_llm()


@lru_cache(maxsize=1)
def get_web_search_tool():
    from src.route.websearch import web_search_tool
    return web_search_tool



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

    # Retrieval - ask for results and keep only the top result (k=1)
    docs = retriever.invoke(question)

    # Normalize to list of Documents
    if hasattr(docs, "page_content"):
        docs_list = [docs]
    elif isinstance(docs, list):
        docs_list = docs
    else:
        docs_list = [docs]

    top_docs = docs_list[:1]
    return {"documents": top_docs, "question": question}

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

    # Normalize documents and use only the top document as context
    if isinstance(documents, Document):
        docs_list = [documents]
    elif isinstance(documents, list):
        docs_list = documents
    else:
        docs_list = [documents]

    top_docs = docs_list[:1]
    context = top_docs[0].page_content if top_docs else ""

    # Generation using only the top document
    generation = rag_chain.invoke({"context": context, "question": question})

    # If the user also asks about AI, fetch a web summary and append it
    ql = question.lower()
    if "ai" in ql or "artificial intelligence" in ql:
        # call web search tool and summarize top result
        web_docs = get_web_search_tool().invoke(question)
        # normalize
        if isinstance(web_docs, str):
            web_text = web_docs
        elif isinstance(web_docs, list):
            if all(isinstance(d, dict) and "content" in d for d in web_docs):
                web_text = web_docs[0]["content"] if web_docs else ""
            elif all(hasattr(d, "page_content") for d in web_docs):
                web_text = web_docs[0].page_content if web_docs else ""
            else:
                web_text = str(web_docs[0]) if web_docs else ""
        elif hasattr(web_docs, "page_content"):
            web_text = web_docs.page_content
        else:
            web_text = str(web_docs)

        if web_text:
            web_summary = rag_chain.invoke({"context": web_text, "question": question})
            combined = f"{generation}\n\nAbout AI:\n{web_summary}"
            return {"documents": top_docs, "question": question, "generation": combined}

    return {"documents": top_docs, "question": question, "generation": generation}


def chat(state):
    """
    Handle normal conversational prompts without RAG/web retrieval.
    """
    print("---CHAT---")
    question = state["question"]
    llm = get_chat_llm()
    generation = llm.invoke(question).content
    return {"documents": [], "question": question, "generation": generation}

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
    docs = get_web_search_tool().invoke(question)

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
