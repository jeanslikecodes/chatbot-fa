# Guia de Futebol Americano — Chatbot de IA Generativa (NVIDIA + Streamlit + Oracle Cloud)

Chatbot de IA generativa que atua como **guia de futebol americano** para iniciantes,
desenvolvido em **Python + Streamlit**, usando um modelo **open source disponibilizado
pela NVIDIA**, publicado em uma **máquina virtual na Oracle Cloud** e acessível via
navegador por um IP público.

- **Aplicação em produção:** http://152.67.43.234:8501
- **Repositório:** https://github.com/jeanslikecodes/chatbot-fa

---

## Instalação e execução (local)

Pré-requisito: Python 3.10+ e uma chave da NVIDIA (gere em https://build.nvidia.com).

```bash
# 1. Clonar o repositório
git clone https://github.com/jeanslikecodes/chatbot-fa.git
cd chatbot-fa

# 2. Criar e ativar um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Configurar a credencial
cp .env.example .env
# edite o .env e cole a sua NVIDIA_API_KEY

# 5. Rodar
streamlit run app.py
```

Acesse `http://localhost:8501` no navegador.

---

# Relatório da Atividade

## Introdução

### Objetivo da atividade
Desenvolver e implantar um chatbot baseado em Inteligência Artificial Generativa
utilizando um modelo **open source disponibilizado pela NVIDIA**. A aplicação foi
construída em Python com Streamlit e publicada em uma máquina virtual na Oracle
Cloud, ficando acessível por um endereço IP público e permitindo a interação de
usuários pelo navegador.

### Visão geral da solução
A solução é uma aplicação web de chat com a persona de um **guia de futebol
americano** para iniciantes: explica regras, posições, jogadas, estratégias e a
terminologia em inglês. O usuário digita mensagens na interface Streamlit; cada
mensagem é enviada, junto ao histórico da conversa, a um modelo de linguagem
hospedado na infraestrutura da NVIDIA (NVIDIA NIM). A resposta é exibida em
**streaming** (token a token), simulando uma conversa fluida. Todo o processamento
pesado do modelo ocorre na nuvem da NVIDIA — a VM apenas serve a interface e faz a
ponte com a API. O comportamento do guia é definido por um *system prompt*
dedicado.

```
Usuário (navegador) ⇄ Streamlit (VM Oracle) ⇄ API NVIDIA (modelo LLM)
```

## Modelo Escolhido

### Nome
`meta/llama-3.1-8b-instruct` — servido via **NVIDIA NIM**
(`https://integrate.api.nvidia.com/v1`).

### Justificativa da escolha
- **Open source e disponibilizado pela NVIDIA**, atendendo diretamente ao requisito
  da atividade.
- **Latência muito baixa** (respostas em dezenas de milissegundos nos testes),
  ideal para uma conversa fluida em tempo real.
- **Disponibilidade confirmada em teste**: inicialmente escolhi outro modelo do catálogo (`meta/llama-3.3-70b-instruct`) porém ele apresentou instabilidade no serviço no momento do desenvolvimento (requisições sem resposta); o 8B respondeu de forma consistente em todos os testes.
- **Compatível com a API no padrão OpenAI**, o que simplifica a integração.
- O tamanho do modelo **não impacta a VM**, pois a inferência é remota.

### Principais características
- 8 bilhões de parâmetros, ajustado para instrução (*instruct*).
- Baixa latência, adequado para aplicações interativas.
- Suporte nativo a *streaming* de tokens.
- Boa qualidade em português para explicações objetivas e diálogo multi-turno.

## Desenvolvimento

### Arquitetura da aplicação
Aplicação de arquivo único (`app.py`) com fluxo simples e legível:

1. Carrega a credencial do `.env`.
2. Instancia um cliente `OpenAI` apontando para a API da NVIDIA (endpoint no padrão
   OpenAI compatível), com um *system prompt* que define o comportamento do assistente.
3. Mantém o **estado da conversa** em `st.session_state` como uma lista de mensagens
   (`system`, `user`, `assistant`), enviada ao modelo a cada turno para preservar o contexto.
4. A cada mensagem, gera a resposta em **streaming** com `st.write_stream`.

### Bibliotecas utilizadas
- **streamlit** — interface web do chat.
- **openai** — SDK oficial usado para falar com a API da NVIDIA via `chat.completions`.
- **python-dotenv** — carrega a chave a partir do arquivo `.env`.

> Optou-se pelo SDK `openai` puro em vez da biblioteca `chatlas`: o provedor OpenAI
> do `chatlas` chama por padrão o endpoint `/responses`, não suportado pelo NIM da
> NVIDIA (que expõe apenas `/chat/completions`), o que causava erro 404.

## Discussão

### Lições aprendidas
- Servir um LLM via API (NVIDIA NIM) permite usar modelos grandes sem GPU própria,
  cabendo numa VM gratuita.
- Em nuvem, a rede (VCN, gateways, Security Lists) é tão importante quanto o servidor.

### Possíveis melhorias futuras
- **RAG** para responder sobre documentos específicos.
- **Autenticação** de usuários e registro de conversas.
- **Seleção de modelo** na interface, comparando diferentes LLMs do catálogo NVIDIA.

---

*Desenvolvido como atividade da pós-graduação em IA Generativa da UFPR.*
