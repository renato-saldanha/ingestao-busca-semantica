# Desafio MBA Engenharia de Software com IA - Full Cycle

Sistema de Ingestao e Busca Semantica utilizando LangChain + PostgreSQL (pgVector).
Permite ingerir documentos PDF em um banco vetorial e fazer perguntas via CLI, com respostas baseadas exclusivamente no conteudo do documento.

## Pre-requisitos

- Python 3.12+
- Docker e Docker Compose
- Chave de API: OpenAI (`OPENAI_API_KEY`) **ou** Google (`GOOGLE_API_KEY`)

## Setup

1. Crie e ative o ambiente virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Instale as dependencias:

```bash
pip install -r requirements.txt
```

3. Configure o arquivo `.env` a partir do exemplo:

**Linux / macOS:**

```bash
cp .env.example .env
```

**Windows (CMD):**

```cmd
copy .env.example .env
```

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

Preencha no `.env`:
- A chave de API do provedor escolhido (`OPENAI_API_KEY` ou `GOOGLE_API_KEY`)
- `DATABASE_URL` — string de conexao com o PostgreSQL (ex: `postgresql+psycopg://postgres:postgres@localhost:5434/rag-mba`)
- `PG_VECTOR_COLLECTION_NAME` — nome da colecao vetorial (ex: `mba_chunks`)
- `PDF_PATH` — caminho para o PDF a ser ingerido (ex: `document.pdf` na raiz do projeto, ou caminho absoluto como `C:\projeto\document.pdf` no Windows)

## Ordem de Execucao

```bash
# 1. Subir o banco de dados
docker compose up -d

# 2. Executar a ingestao do PDF
python src/ingest.py

# 3. Iniciar o chat interativo
python src/chat.py
```

## Provedores Suportados

| Provedor | Embedding Model | LLM Model |
|----------|----------------|-----------|
| OpenAI   | `text-embedding-3-small` | `gpt-5-nano` |
| Google   | `models/embedding-001` | `gemini-2.5-flash-lite` |

O sistema detecta automaticamente qual provedor usar com base na presenca da variavel `OPENAI_API_KEY` no `.env`. Se presente, usa OpenAI; caso contrario, usa Google.

> **Importante**: Os embeddings de OpenAI (1536 dimensoes) e Google (768 dimensoes) sao incompativeis. Ao trocar de provedor, e necessario re-executar `python src/ingest.py` para recriar os vetores. A colecao anterior e automaticamente limpa (`pre_delete_collection=True`).

## Exemplos de Uso

### Pergunta dentro do contexto do PDF

```
Faca sua pergunta: Quais as 10 empresas que mais faturam?

PERGUNTA: Quais as 10 empresas que mais faturam?
RESPOSTA: [resposta baseada no conteudo do documento]
```

### Pergunta fora do contexto (dados inexistentes)

```
Faca sua pergunta: Quantos clientes temos em 2024?

PERGUNTA: Quantos clientes temos em 2024?
RESPOSTA: Nao tenho informacoes necessarias para responder sua pergunta.
```

### Pergunta de opiniao/interpretacao

```
Faca sua pergunta: Voce acha isso bom ou ruim?

PERGUNTA: Voce acha isso bom ou ruim?
RESPOSTA: Nao tenho informacoes necessarias para responder sua pergunta.
```

### Pergunta sem relacao com o documento

```
Faca sua pergunta: Qual e a capital da Franca?

PERGUNTA: Qual e a capital da Franca?
RESPOSTA: Nao tenho informacoes necessarias para responder sua pergunta.
```

## Troubleshooting

| Problema | Solucao |
|----------|---------|
| Erro de conexao com banco | Verificar se o container esta ativo (`docker compose ps`) e se `DATABASE_URL` esta correto no `.env` |
| Erro de API key | Conferir a variavel no `.env` — sem espacos ou quebras de linha extras |
| Erro de colecao vetorial | Confirmar que `PG_VECTOR_COLLECTION_NAME` e o mesmo na ingestao e busca |
| Erro ao ler PDF | Validar o caminho em `PDF_PATH` e permissoes do arquivo |
| Respostas vazias ou ruins | Re-executar `python src/ingest.py` e verificar se os chunks foram persistidos |
| Troca de provedor (OpenAI/Google) | Re-executar `python src/ingest.py` apos alterar o provedor no `.env` |
