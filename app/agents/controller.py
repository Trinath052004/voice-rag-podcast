from app.services.llm import call_gemini
from app.rag.retriever import retrieve
from app.agents.curious_agent import curious_prompt
from app.agents.explainer_agent import explainer_prompt, explainer_wrap_up_prompt

def run_podcast_turn(topic: str = "overview") -> dict:
    """
    Auto-generated podcast turn between Curious and Explainer.
    User can interject via run_user_question().
    """
    # Retrieve context
    contexts = retrieve(topic, top_k=5)
    context = "\n\n".join(contexts)
    
    # Curious asks
    question = call_gemini(curious_prompt(context))
    
    # Explainer answers with wrap-up
    answer = call_gemini(explainer_prompt(context, question, should_wrap_up=True))
    
    return {
        "curious": question,
        "explainer": answer,
        "answer": answer
    }

def run_user_question(user_input: str) -> dict:
    """
    User (third party) interjects with their own question.
    Explainer answers and wraps up.
    """
    contexts = retrieve(user_input, top_k=5)
    context = "\n\n".join(contexts)
    
    # Explainer answers user's question with wrap-up
    answer = call_gemini(explainer_prompt(context, user_input, should_wrap_up=True))
    
    return {
        "user_question": user_input,
        "explainer": answer,
        "answer": answer
    }

def run_multi_turn_podcast(topic: str = "overview", num_turns: int = 3) -> list:
    """
    Generate multiple podcast turns for a longer episode.
    """
    turns = []
    for i in range(num_turns):
        is_last = (i == num_turns - 1)
        contexts = retrieve(topic, top_k=5)
        context = "\n\n".join(contexts)
        
        question = call_gemini(curious_prompt(context))
        answer = call_gemini(explainer_prompt(context, question, should_wrap_up=is_last))
        
        turns.append({
            "turn": i + 1,
            "curious": question,
            "explainer": answer
        })
    
    return turns