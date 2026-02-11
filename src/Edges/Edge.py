### Edges ###
from src.route.route import question_router
from src.llms.llm import Groqllm
from src.route.GradeHallucination import hallucination_grader
from src.route.GradeAnswer import answer_grader


def route_question(state):
    """
    Route question to web search or RAG.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """

    print("---ROUTE QUESTION---")
    question = state["question"]

    # Attempt to use the trained router; fall back to a simple heuristic
    # if the model fails to call a tool or returns an unexpected value.
    try:
        source = question_router.invoke({"question": question})
        ds = getattr(source, "datasource", None)
    except Exception as e:
        print("Router failed, falling back to heuristic:", e)
        ds = None

    # Normalize possible values and fall back to heuristic when needed
    if ds in ("web_search", "websearch", "web-search"):
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return "web_search"
    if ds in ("vectorstore", "vector_store", "vector-store"):
        print("---ROUTE QUESTION TO RAG---")
        return "vectorstore"

    # Heuristic fallback: school-related keywords -> vectorstore, else web_search
    ql = question.lower()
    school_keywords = ["sunmark", "school", "admission", "fees", "principal", "campus", "curriculum", "ib", "a-level", "a level", "btec"]
    if any(k in ql for k in school_keywords):
        print("---ROUTER FALLBACK: choosing RAG (vectorstore)---")
        return "vectorstore"

    print("---ROUTER FALLBACK: choosing WEB SEARCH---")
    return "web_search"


def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    print("---ASSESS GRADED DOCUMENTS---")
    state["question"]
    filtered_documents = state["documents"]

    if not filtered_documents:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"


def grade_generation_v_documents_and_question(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]

    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )
    grade = score.binary_score

    # Check hallucination
    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        # Check question-answering
        print("---GRADE GENERATION vs QUESTION---")
        score = answer_grader.invoke({"question": question, "generation": generation})
        grade = score.binary_score
        if grade == "yes":
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"