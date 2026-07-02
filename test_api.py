import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

print("Chave lida do .env:", (os.getenv("NVIDIA_API_KEY") or "NENHUMA")[:12], "...")

client = OpenAI(
    api_key=os.getenv("NVIDIA_API_KEY"),
    base_url="https://integrate.api.nvidia.com/v1",
    timeout=30,  # não trava para sempre; erro após 30s
)

print("Chamando a API (stream)...")

stream = client.chat.completions.create(
    model="meta/llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "responda apenas: ok"}],
    max_tokens=20,
    stream=True,
)

print("Resposta: ", end="", flush=True)
for chunk in stream:
    if not chunk.choices:
        continue
    conteudo = chunk.choices[0].delta.content
    if conteudo:
        print(conteudo, end="", flush=True)
print("\n--- FIM ---")
