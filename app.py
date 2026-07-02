import os
import re

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "meta/llama-3.1-8b-instruct"
BASE_URL = "https://integrate.api.nvidia.com/v1"

RECUSA_PADRAO = "Meu foco é futebol americano — quer saber algo sobre o esporte?"

PADROES_SUSPEITOS = [
    r"repita.*(instru|regra|prompt|acima)",
    r"revele.*(instru|regra|prompt)",
    r"resuma.*(instru|regra|prompt)",
    r"traduza.*(instru|regra|prompt)",
    r"ignore.*(instru|regra)",
    r"esque(ç|c)a.*(instru|regra)",
    r"system\s*override",
    r"modo de auditoria",
    r"sem restri(ç|c)(õ|o)es",
    r"sem filtro",
]

def mensagem_suspeita(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(re.search(padrao, texto_lower) for padrao in PADROES_SUSPEITOS)

def _normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.lower()).strip()

def contem_vazamento_de_prompt(texto: str, janela: int = 30, passo: int = 8) -> bool:
    """Detecta se a RESPOSTA do modelo reproduziu trechos do próprio
    system prompt — pega vazamentos mesmo quando a pergunta do usuário
    escapou do filtro de entrada (ex.: pedidos via história/ficção).

    Comparação por janelas curtas (não por linha inteira): um trecho de
    30+ caracteres reaproveitado ao pé da letra já é detectado, mesmo que
    o resto da frase ao redor tenha sido reescrito/parafraseado."""
    texto_norm = _normalizar(texto)
    prompt_norm = _normalizar(SYSTEM_PROMPT)
    for i in range(0, len(prompt_norm) - janela, passo):
        if prompt_norm[i : i + janela] in texto_norm:
            return True
    return False

st.set_page_config(
    page_title="Guia de Futebol Americano",
    page_icon="🏈",
    layout="centered",
)

st.title("🏈 Guia de Futebol Americano")
st.caption("Tire suas dúvidas sobre futebol americano")

CAMINHO_SYSTEM_PROMPT = "system_prompt.txt"

if not os.path.exists(CAMINHO_SYSTEM_PROMPT):
    st.error(
        f"Arquivo '{CAMINHO_SYSTEM_PROMPT}' não encontrado. "
        "Crie-o a partir de system_prompt.example.txt (veja o README)."
    )
    st.stop()

with open(CAMINHO_SYSTEM_PROMPT, encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

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

MAX_HISTORICO = 12  # últimas mensagens (excluindo o system prompt) enviadas ao modelo

def gerar_resposta():
    # Trunca o histórico enviado à API: em conversas longas, um modelo pequeno
    # tende a "seguir o tom" das últimas trocas e se afastar das regras do
    # system prompt. Reenviá-lo sempre por completo, com uma janela curta de
    # histórico, mantém o comportamento firme.
    mensagens_api = [st.session_state.messages[0]] + st.session_state.messages[1:][-MAX_HISTORICO:]
    stream = client.chat.completions.create(
        model=MODEL,
        messages=mensagens_api,
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

    with st.chat_message("assistant"):
        if mensagem_suspeita(pergunta):
            resposta = RECUSA_PADRAO
            st.markdown(resposta)
        else:
            with st.spinner("Pensando..."):
                texto_acumulado = ""
                try:
                    for pedaco in gerar_resposta():
                        texto_acumulado += pedaco
                    if contem_vazamento_de_prompt(texto_acumulado):
                        resposta = RECUSA_PADRAO
                    else:
                        resposta = texto_acumulado
                except Exception as erro:
                    resposta = None
                    st.error(f"Falha ao chamar a API da NVIDIA: {erro}")
            if resposta:
                st.markdown(resposta)

    # Guarda a resposta no histórico (contexto das próximas mensagens).
    if resposta:
        st.session_state.messages.append({"role": "assistant", "content": resposta})
