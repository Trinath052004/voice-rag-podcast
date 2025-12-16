from app.services.embeddings import embed_texts
from app.rag.retriever import retrieve
from app.services.vertex_llm import ask_gemini
from app.agents.curious_agent import curious_prompt
from app.agents.explainer_agent import explainer_prompt

def run_turn(user_input=None):
    if user_input:
        q_vec = embed_texts([user_input])[0]
        ctx = "\n".join(retrieve(q_vec))
        return ask_gemini(explainer_prompt(ctx, user_input))

    seed_vec = embed_texts(["overview"])[0]
    ctx = "\n".join(retrieve(seed_vec))

    question = ask_gemini(curious_prompt(ctx))
    answer = ask_gemini(explainer_prompt(ctx, question))

    return {
        "curious": question,
        "explainer": answer
    }
