from src.rags.rag import create_rag_chain, create_vector_store, load_csv
from src.llms.model import Groqllm


if __name__ == "__main__":
    docs = load_csv()
    vectorstore = create_vector_store(docs)
    rag_chain = create_rag_chain(vectorstore)

    query = "Where is Sunmarke School’s campus located in Dubai?"
    
    # For LCEL, invoke with just the question string
    result = rag_chain.invoke(query)

    print("Answer:")
    print(result)