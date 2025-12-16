from vertexai.preview.generative_models import GenerativeModel

model = GenerativeModel("gemini-1.5-pro")

def ask_gemini(prompt: str):
    return model.generate_content(prompt).text
