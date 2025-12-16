def build_conversation_prompt(context_chunks, user_question):
    context = "\n\n".join(context_chunks)

    return f"""
You are simulating a thoughtful, podcast-style conversation.

Participants:
- Curious Agent: asks insightful follow-up questions.
- Explainer Agent: gives clear, structured explanations.
- User: asked the original question.

Rules:
- Use ONLY the context provided.
- Do NOT hallucinate.
- If information is missing, say so clearly.
- Keep the tone natural and conversational.

Context from documents:
------------------------
{context}
------------------------

User Question:
{user_question}

Conversation (start now):

Curious Agent:
Explainer Agent:
"""
