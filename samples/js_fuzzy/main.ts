import OpenAI from "openai";

const client = new OpenAI({ apiKey: "local" });

export async function classifyLabel(input: string): Promise<string> {
  const prompt = `Match this request to one label (billing, support, sales). Use synonyms where needed: ${input}`;
  const out = await client.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: prompt }],
  });
  return out.choices[0].message.content ?? "support";
}
