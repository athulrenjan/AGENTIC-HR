from groq import Groq, RateLimitError
from app.config import GROQ_API_KEY, MODEL

client = Groq(api_key=GROQ_API_KEY)

def call_llm(prompt: str) -> str:
    try:
        res = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert HR recruiter assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return res.choices[0].message.content
    except RateLimitError as e:
        # Handle rate limit by raising a custom exception
        raise RuntimeError(f"Groq API rate limit exceeded: {str(e)}. Please upgrade your plan or try again later.")
