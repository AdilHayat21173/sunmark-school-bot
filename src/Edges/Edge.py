### Edges ###
from src.route.route import question_router
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

    # Heuristic short-circuit first for stability on simple prompts.
    ql = question.lower()
    stripped = ql.strip()
    school_keywords = [
        "sunmark", "sunmarke", "school", "admission", "fees", "principal",
        "campus", "curriculum", "ib", "a-level", "a level", "btec"
    ]
    web_lookup_keywords = [
        "today", "latest", "current", "news", "weather", "stock", "price",
        "recent", "update", "headline"
    ]
    casual_keywords = [
        "hi", "hello", "hey", "how are you", "who are you", "thank you",
        "thanks", "good morning", "good evening", "what can you do"
    ]
    casual_exact = {"hi", "hello", "hey", "yo", "sup", "thanks", "thank you"}

    if stripped in casual_exact or any(k in ql for k in casual_keywords):
        print("---ROUTER HEURISTIC: choosing CHAT---")
        return "chat"
    if any(k in ql for k in school_keywords):
        print("---ROUTER HEURISTIC: choosing RAG (vectorstore)---")
        return "vectorstore"
    if any(k in ql for k in web_lookup_keywords):
        print("---ROUTER HEURISTIC: choosing WEB SEARCH---")
        return "web_search"

    # Attempt to use the trained router for ambiguous prompts.
    try:
        source = question_router.invoke({"question": question})
        ds = getattr(source, "datasource", None)
    except Exception as e:
        print("Router failed, falling back to chat:", e)
        ds = None

    if ds in ("web_search", "websearch", "web-search"):
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return "web_search"
    if ds in ("vectorstore", "vector_store", "vector-store"):
        print("---ROUTE QUESTION TO RAG---")
        return "vectorstore"
    if ds in ("chat", "conversation", "normal_chat"):
        print("---ROUTE QUESTION TO CHAT---")
        return "chat"

    print("---ROUTER DEFAULT: choosing CHAT---")
    return "chat"


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
