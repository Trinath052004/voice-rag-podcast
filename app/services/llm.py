
import os
from dotenv import load_dotenv
import google.generativeai as genai
from app.rag.retriever import retrieve
import logging

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-flash-latest")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def call_gemini(question: str):
    try:
        contexts = retrieve(question, top_k=3)

        if not contexts:
            context_text = "No relevant context found."
        else:
            context_text = "\n\n".join(contexts)

        # Improved prompt with clear instructions and formatting
        prompt = f"""You are a helpful and informative podcast assistant.
        Your goal is to answer the user's question based on the context provided.
        If the context does not contain the answer, respond with "I don't know".
        Please provide a concise and accurate answer.

        Context:\n{context_text}

        Question:\n{question}

        Answer:"""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error during Gemini call: {e}")
        return "I don't know"

