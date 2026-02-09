from openai import OpenAI


client = OpenAI()


def summarize_long_report(report: str) -> str:
    prompt = (
        "Provide a long-form nuanced summary preserving style and context, "
        "including contradictions and implicit themes."
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt + "\n" + report}],
    )
    return resp.choices[0].message.content
