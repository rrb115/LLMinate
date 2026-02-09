from anthropic import Anthropic


client = Anthropic()


def extract_profile(raw: str) -> str:
    return client.messages.create(
        model="claude-mock",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": f"Extract fields as JSON only: name, email, id from: {raw}",
            }
        ],
    )
