from openai import OpenAI


client = OpenAI()


def classify_ticket(text: str) -> str:
    prompt = f"Determine if this ticket should be escalated: {text}. Respond with ONLY YES or NO"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()
