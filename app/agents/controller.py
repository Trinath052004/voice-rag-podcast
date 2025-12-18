
from app.services.llm import call_gemini
from app.rag.retriever import retrieve
from app.agents.curious_agent import curious_prompt
from app.agents.explainer_agent import explainer_prompt, explainer_wrap_up_prompt
import logging
from typing import List, Tuple


def run_podcast_turn(topic: str = "overview") -> dict:
    """
    Auto-generated podcast turn between Curious and Explainer.
    User can interject via run_user_question().
    """
    if not topic:
        logging.warning("Topic cannot be empty.")
        return {"error": "Topic cannot be empty."}

    # Retrieve context with scores
    contexts_with_scores: List[Tuple[str, float]] = retrieve(topic, top_k=5)

    if not contexts_with_scores:
        context = "No relevant context found."
    else:
        # Select contexts based on scores (e.g., take top 3)
        selected_contexts = [text for text, score in contexts_with_scores[:3]]
        context = "\n\n".join(selected_contexts)

    # Curious asks
    question = call_gemini(curious_prompt(context))

    # Explainer answers with wrap-up
    answer = call_gemini(explainer_prompt(context, question, should_wrap_up=True))

    return {
        "curious": question,
        "explainer": answer,
        "answer": answer,
    }


def run_user_question(user_input: str) -> dict:
    """
    User (third party) interjects with their own question.
    Explainer answers and wraps up.
    """
    if not user_input:
        logging.warning("User input cannot be empty.")
        return {"error": "User input cannot be empty."}

    # Retrieve context with scores
    contexts_with_scores: List[Tuple[str, float]] = retrieve(user_input, top_k=5)

    if not contexts_with_scores:
        context = "No relevant context found."
    else:
        # Select contexts based on scores (e.g., take top 3)
        selected_contexts = [text for text, score in contexts_with_scores[:3]]
        context = "\n\n".join(selected_contexts)

    # Explainer answers user's question with wrap-up
    answer = call_gemini(explainer_prompt(context, user_input, should_wrap_up=True))

    return {
        "user_question": user_input,
        "explainer": answer,
        "answer": answer,
    }


def _generate_podcast_turn(topic: str, is_last: bool) -> dict:
    """
    Generates a single turn of the podcast.
    """
    # Retrieve context with scores
    contexts_with_scores: List[Tuple[str, float]] = retrieve(topic, top_k=5)

    if not contexts_with_scores:
        context = "No relevant context found."
    else:
        # Select contexts based on scores (e.g., take top 3)
        selected_contexts = [text for text, score in contexts_with_scores[:3]]
        context = "\n\n".join(selected_contexts)

    question = call_gemini(curious_prompt(context))
    answer = call_gemini(explainer_prompt(context, question, should_wrap_up=is_last))
    return {
        "curious": question,
        "explainer": answer,
    }


def run_multi_turn_podcast(topic: str = "overview", num_turns: int = 3) -> list:
    """
    Generate multiple podcast turns for a longer episode.
    """
    turns = []
    for i in range(num_turns):
        is_last = (i == num_turns - 1)
        turn = _generate_podcast_turn(topic, is_last)
        turns.append({
            "turn": i + 1,
            **turn,
        })
    return turns