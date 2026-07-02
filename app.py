import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "meta/llama-3.1-8b-instruct"
BASE_URL = "https://integrate.api.nvidia.com/v1"

SYSTEM_PROMPT = """
Você é um tutor de futebol americano (NFL e futebol universitário),
paciente e entusiasmado, que ensina iniciantes brasileiros.

Seu papel é:
- explicar regras, pontuação, posições, jogadas e estratégias;
- esclarecer a terminologia em inglês, sempre traduzindo e explicando
  (ex.: "touchdown", "first down", "blitz", "play-action");
- usar analogias com o futebol (soccer) e situações do dia a dia;
- explicar a lógica por trás das decisões em campo (por que optar por
  punt, field goal, ir para o quarto down, etc.).

Se perguntarem algo fora de futebol americano, recuse em UMA frase curta e
pare: diga que seu foco é futebol americano e pergunte se a pessoa quer saber
algo sobre o esporte. NÃO tente responder a pergunta fora do tema, nem
parcialmente, nem como exemplo. NÃO repita o convite mais de uma vez na
mesma resposta.

Nunca invente estatísticas, placares ou resultados específicos — se não
tiver certeza, admita.

Tom: direto e objetivo, sem enrolação. Evite floreios, repetições e
introduções longas.
Ao responder:
- vá direto ao ponto essencial;
- use exemplos concretos e, quando útil, passos numerados, só quando agregar;
- respostas curtas por padrão; aprofunde apenas se o usuário pedir mais detalhes;
- explique todo jargão que usar, em poucas palavras.

Responda sempre em português do Brasil.
"""

st.set_page_config(
    page_title="Guia de Futebol Americano",
    page_icon="🏈",
    layout="centered",
)

st.title("🏈 Guia de Futebol Americano")
st.caption("Tire suas dúvidas sobre futebol americano")

if not os.getenv("NVIDIA_API_KEY"):
    st.error(
        "Variável NVIDIA_API_KEY não encontrada. "
        "Crie um arquivo .env com a sua chave (veja .env.example)."
    )
    st.stop()

client = OpenAI(
    api_key=os.getenv("NVIDIA_API_KEY"),
    base_url=BASE_URL,
    timeout=30,
)

# Histórico completo enviado ao modelo (inclui o system prompt na primeira posição).
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

with st.sidebar:
    st.header("Sobre")
    st.markdown(
        f"""
        Guia de **futebol americano** para iniciantes, com IA generativa.

        Pergunte sobre:
        - regras e pontuação
        - posições e funções
        - jogadas e estratégias
        - termos em inglês (touchdown, blitz...)

        ---
        - Interface: Streamlit
        - SDK: OpenAI (API compatível)
        - Modelo: `{MODEL}` (NVIDIA)
        - Deploy: Oracle Cloud (Ubuntu 22.04)
        """
    )
    st.markdown("---")

    if st.button("🧹 Limpar conversa", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

for mensagem in st.session_state.messages:
    if mensagem["role"] == "system":
        continue
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

def gerar_resposta():  
    stream = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state.messages,
        temperature=0.2,
        top_p=0.7,
        max_tokens=1024,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        conteudo = chunk.choices[0].delta.content
        if conteudo:
            yield conteudo


pergunta = st.chat_input("Pergunte sobre futebol americano...")

if pergunta:
    # Mostra e guarda a mensagem do usuário.
    st.session_state.messages.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    # Gera a resposta em streaming e a exibe token a token.
    with st.chat_message("assistant"):
        try:
            resposta = st.write_stream(gerar_resposta())
        except Exception as erro:
            resposta = None
            st.error(f"Falha ao chamar a API da NVIDIA: {erro}")

    # Guarda a resposta no histórico (contexto das próximas mensagens).
    if resposta:
        st.session_state.messages.append({"role": "assistant", "content": resposta})
