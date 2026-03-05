import os
from util import validate_env
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector

validate_env(script_file=__file__, context="ingest", validate_paths=True)

# Define as variáveis de ambiente
PDF_PATH = os.getenv("PDF_PATH")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
GOOGLE_EMBEDDING_MODEL = os.getenv("GOOGLE_EMBEDDING_MODEL")
PG_VECTOR_COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")
DATABASE_URL= os.getenv("DATABASE_URL")


def get_embeddings():
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    return GoogleGenerativeAIEmbeddings(model=GOOGLE_EMBEDDING_MODEL)


# Carrega o documento PDF
def load_doc() -> List[Document]:
    """
    Método que carrega um documento PDF utilizando a constante PDF_PATH (caminho do documento)
    Define o loader
    Carrega o documento
    Retorna o documento

    Result:
        docs -> PyPDFLoader
    """

    print("Iniciando a carga do documento.")

    try:
        # Define o loader com o caminho do documento PDF
        loader = PyPDFLoader(PDF_PATH)

        # Carrega o documento
        docs = loader.load()

        # Valida o documento
        if not docs:
            print("Não há documento carregado.")
            raise SystemExit(0)

        return docs
    except FileNotFoundError as e:
        print(f"PDF não encontrado: {e}")
        raise SystemExit(1)
    except PermissionError as e:
        print(f"Sem permissão para ler o arquivo: {e}")
        raise SystemExit(1)
    except Exception as e:
        print(f"Erro ao carregar PDF: {e}")
        raise SystemExit(1)    


# Carrega as chunks 
def load_chunks(docs: List[Document]) -> List[Document]:
    """
    Método que carrega as chunks com base no documento informado
    Define o splitter usando modo recursivo. Params: chunk_size=1000 e chunk_overlap=150
    Define as chunks
    Retorna as chunks

    Args:
        docs-> List[Document]
    Result:
        chunks-> List[Document]    
    """

    print("Iniciando a carga dos chunks.")

    try:
        # Define o splitter utilizando o splitter recursivo
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            add_start_index=False)

        # Define os chunks
        chunks = splitter.split_documents(docs)
        
        # Valida se os chunks foram processados corretamente
        if not chunks:
            print("Chunks não processados.")
            raise SystemExit(0)

        # Remove ruído do documento
        enriched_chunks = [
            Document(
                page_content=d.page_content,
                metadata={k: v for k, v in d.metadata.items() if v not in ("", None)}
            )
            for d in chunks
        ]   

        return enriched_chunks
    except TypeError as e:
        print(f"Documentos inválidos: {e}")
        raise SystemExit(1)
    except AttributeError as e:
        print(f"Estrutura do documento inválida: {e}")
        raise SystemExit(1)
    except ValueError as e:
        print(e)
        raise SystemExit(1)


# Faz o injest do PDF no banco
def ingest_pdf():
    """
    Metodo que define o embeddings
    Define a store do PGVector
    Adiciona à store os chunks

    Args:
      chunks-> List[Document]
    """

    print("Iniciando o injest.")

    try:
        # Define o embeddings
        embeddings = get_embeddings()

        # Define o store do PGVector
        store = PGVector(
            embeddings=embeddings,
            collection_name=PG_VECTOR_COLLECTION_NAME,
            connection=DATABASE_URL,
            use_jsonb=True,
            pre_delete_collection=True,
        )

        # Carrega o documento
        docs = load_doc()

        # Carrega o chunks
        chunks = load_chunks(docs)

        # Adiciona ao store
        store.add_documents(chunks)

        print("Injest concluído.")
        print(f"Total de chunks: {len(chunks)}.")
        print(f"Total de paginas: {len(docs)}.")    
        print(f"Collection Name: {PG_VECTOR_COLLECTION_NAME}.")
    except FileNotFoundError as e:
        print(f"Arquivo não encontrado: {e}")
        raise SystemExit(1)
    except RuntimeError as e:
        print(f"Erro de configuração: {e}")
        raise SystemExit(1)
    except Exception as e:
        print(f"Erro inesperado: {e}")
        raise
    

if __name__ == "__main__":
    ingest_pdf()