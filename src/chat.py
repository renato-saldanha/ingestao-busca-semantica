from search import search_prompt

import re


def pergunta_invalida(texto: str) -> bool:
    """
    Valida se o texto parece uma perunta.
    """
    # Valida texto vazio
    if not texto or not texto.strip():
        print("Favor informar uma pergunta.")
        return True
    
    # Cria padrão básico de verificação de questionamento váilido
    padrao = re.compile(
        r'^(.{3,}\?|(o que|como|qual|quais|quando|onde|por que|quem)\b.+)',
        re.IGNORECASE
    )

    # Define variável
    padrao_valido = bool(padrao.match(texto.strip()))

    # Valida padrão inválido
    if not padrao_valido:
        print("Favor reformular sua pergunta.")
        return True

    return False


def main():
    # Define os comandos padrões
    COMANDOS = ["sair", "exit", "quit"]

    # Inicializa a variável
    question = None
    
    # Loop de processamento
    while not question in COMANDOS:
        question = input("Faça sua pergunta: ")

        # Valida se é comando
        if question in COMANDOS:
            break
        
        # Valida possíveis perguntas válidas
        if pergunta_invalida(question):   
            question = None
            continue

        # Retorna o resultado da pergunta
        try:
            result = search_prompt(question)
        except Exception as e:
            print(f"Erro ao processar pergunta: {e}")
            question = None
            continue

        # Imprime no terminal
        print(f"\nPERGUNTA: {question}")
        print(f"RESPOSTA: {result}\n")

if __name__ == "__main__":
    main()