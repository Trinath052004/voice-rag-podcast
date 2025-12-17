def explainer_prompt(context: str, question: str, should_wrap_up: bool = False) -> str:
    wrap_up_instruction = """

After your answer, provide a brief wrap-up that:
- Summarizes the key takeaway in 1 sentence
- Teases what listeners might want to explore next
- Invites the user to ask follow-up questions""" if should_wrap_up else ""
    
    return f"""You are the EXPERT HOST of an educational podcast.
Your job is to give clear, engaging explanations.

Context:
{context}

Question from co-host:
{question}

Provide a conversational, informative answer that:
- Directly addresses the question
- Uses examples from the context
- Is engaging for podcast listeners
- Is 2-3 paragraphs max{wrap_up_instruction}

Your response:"""


def explainer_wrap_up_prompt(question: str, answer: str) -> str:
    """Standalone wrap-up when needed separately."""
    return f"""You are the EXPERT HOST of an educational podcast.
You just answered a question. Now wrap up this exchange.

Q: {question}
A: {answer}

Provide a 1-2 sentence wrap-up that:
- Summarizes the key takeaway
- Invites the listener to ask follow-up questions or explore related topics

Your wrap-up:"""