import os
import google.generativeai as genai
from app.rag.retriever import retrieve

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel("gemini-flash-latest")


def generate_response(question: str):
    contexts = retrieve(question, top_k=3)

    if not contexts:
        context_text = "No relevant context found."
    else:
        context_text = "\n\n".join(contexts)

    prompt = f"""
You are an assistant that answers ONLY using the context below.
If the answer is not in the context, say "I don't know".

Context:
{context_text}

Question:
{question}

Answer:
"""

    response = model.generate_content(prompt)
    return response.text




