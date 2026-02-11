from src.graphs.graph import app

if __name__ == "__main__":
    # Example question
    question = "Tell me about the sunmark school "

    # Run the graph with the initial state containing the question
    final_state = app.invoke({"question": question})

    print("\n" + "="*70)
    print("FINAL STATE")
    print("="*70)
    print(final_state)
