def explainer_prompt(context, question):
    return f"""
You are an expert explainer.
Answer ONLY from the document context.

Context:
{context}

Question:
{question}
"""
