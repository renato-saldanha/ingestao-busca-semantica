import os
from util import validate_env
from typing import List

from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_postgres import PGVector

validate_env(script_file=__file__, context="search", validate_paths=False)

# Define as variáveis de ambiente
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
OPENAI_AI_MODEL = os.getenv("OPENAI_AI_MODEL")
GOOGLE_EMBEDDING_MODEL = os.getenv("GOOGLE_EMBEDDING_MODEL")
GOOGLE_AI_MODEL = os.getenv("GOOGLE_AI_MODEL")
PG_VECTOR_COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")
DATABASE_URL= os.getenv("DATABASE_URL")


def get_embeddings():
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    return GoogleGenerativeAIEmbeddings(model=GOOGLE_EMBEDDING_MODEL)


def get_llm():
    if os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model=OPENAI_AI_MODEL, temperature=0.2)
    return ChatGoogleGenerativeAI(model=GOOGLE_AI_MODEL, temperature=0.2)

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações fora do CONTEXTO fornecido.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO" SOMENTE COM BASE NO CONTEXTO
"""

# Faz busca por similaridade no store
def search_prompt(question=None):
  """
  Metodo que chama a busca por similaridade 
  Define Embeddings
  Define store
  Faz busca por similaridade topK=10
  Retorna a melhor resposta.

  Args:
    question-> "Quais as 10 empresas com maior faturamento?"      
  """

  
  try:
    # Define o embeddings
    embeddings = get_embeddings()

    # Define a store
    store = PGVector(
      embeddings=embeddings,
      collection_name=PG_VECTOR_COLLECTION_NAME,
      connection=DATABASE_URL,
      use_jsonb=True,      
    )

    # Faz conversão do texto
    def format_docs(docs):
      return "\n\n".join(doc.page_content for doc in docs)

    # Formata o retriever
    def retrieve_and_format(question=None)-> List[Document]:
      """
      Recebe a busca e formata como documento

      Args:
        question-> 
      """

      results = store.similarity_search_with_score(question, k=10)
      docs = [doc for doc, _ in results]

      return format_docs(docs)
    
    # Define o prompt
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    # Define a llm
    llm = get_llm()

    # Define a chain
    chain = (
      {"contexto": retrieve_and_format,
        "pergunta": RunnablePassthrough()}
      | prompt
      | llm
      | StrOutputParser()
    )

    result = chain.invoke(question)

    return result

  except ConnectionError as e:
      print("Banco de dados indisponível. Execute: docker compose up -d")
      raise
  except Exception as e:
      if "authentication" in str(e).lower() or "api key" in str(e).lower():
          print("API key inválida. Verifique OPENAI_API_KEY no .env")
      elif "rate limit" in str(e).lower():
          print("Limite de requisições excedido. Aguarde e tente novamente.")
      raise


def main():
    print(search_prompt("Quais as 10 empresas que mais faturam?"))


if __name__ == "__main__":
    main()