from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

resp = client.chat.completions.create(
    model="qwen2.5:7b-instruct",
    messages=[
        {"role": "user", "content": "用一句话解释基金"}
    ]
)

print(resp.choices[0].message.content)
