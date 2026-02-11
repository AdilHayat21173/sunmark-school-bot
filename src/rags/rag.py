from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import json
import os
from pathlib import Path

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent

# Vectorstore path
VECTORSTORE_PATH = BASE_DIR / "sunmarke_faiss_index"

def load_existing_vectorstore():
    """Load previously saved vectorstore"""
    print("="*70)
    print("LOADING EXISTING VECTORSTORE")
    print("="*70)
    print(f"✓ Found existing vectorstore at: {VECTORSTORE_PATH}")
    print("  Loading...\n")
    
    embd = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    vectorstore = FAISS.load_local(
        VECTORSTORE_PATH, 
        embd,
        allow_dangerous_deserialization=True
    )
    
    retriever = vectorstore.as_retriever()
    print("✓ Vectorstore loaded successfully!\n")
    
    return vectorstore, retriever

def create_new_vectorstore():
    """Create new vectorstore from JSON"""
    print("="*70)
    print("CREATING NEW VECTORSTORE")
    print("="*70)
    
    # Construct path to JSON file
    json_file_path = BASE_DIR / "school_data_cleaned.json"
    if not os.path.exists(json_file_path):
        print(f"⚠ Cleaned file not found, using original...")
        json_file_path = BASE_DIR / "school_data.json"

    print(f"Loading JSON file: {json_file_path}\n")

    # Initialize embeddings
    print("Loading Hugging Face embeddings model...")
    embd = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    print("✓ Embeddings model loaded successfully!\n")

    # Load JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Total records: {len(data)}")

    # Convert to Document objects
    docs_list = []
    for record in data:
        doc = Document(
            page_content=record.get('content', ''),
            metadata={
                "id": record.get('id', 0),
                "url": record.get('url', ''),
                "section": record.get('section', ''),
                "subsection": record.get('subsection', '')
            }
        )
        docs_list.append(doc)

    print(f"✓ Created {len(docs_list)} documents from JSON\n")

    # Split documents
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500, 
        chunk_overlap=0
    )
    doc_splits = text_splitter.split_documents(docs_list)
    print(f"✓ Created {len(doc_splits)} document chunks\n")

    # Create vectorstore
    print("Creating FAISS vectorstore...")
    vectorstore = FAISS.from_documents(
        documents=doc_splits,
        embedding=embd
    )
    print("✓ Vectorstore created successfully!\n")

    # Save vectorstore
    print("Saving vectorstore to disk...")
    vectorstore.save_local(VECTORSTORE_PATH)
    print(f"✓ Vectorstore saved to '{VECTORSTORE_PATH}'\n")

    # Create retriever
    retriever = vectorstore.as_retriever()
    
    print("="*70)
    print("VECTORSTORE CREATED AND SAVED")
    print("="*70 + "\n")
    
    return vectorstore, retriever

def get_vectorstore(force_recreate=False):
    """
    Get vectorstore - load existing or create new
    
    Args:
        force_recreate (bool): If True, recreate even if exists
    
    Returns:
        tuple: (vectorstore, retriever)
    """
    
    # Check if vectorstore exists and we don't want to force recreate
    if VECTORSTORE_PATH.exists() and not force_recreate:
        return load_existing_vectorstore()
    else:
        return create_new_vectorstore()

