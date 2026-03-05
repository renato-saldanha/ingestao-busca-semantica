import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


def _resolve_env_path(script_file: Optional[str] = None) -> Path:
    """Localiza o .env tentando múltiplos caminhos (terminal e debugger)."""
    candidates: List[Path] = []
    if script_file:
        script_path = Path(script_file).resolve()
        candidates.append(script_path.parent.parent / ".env")
    candidates.append(Path.cwd() / ".env")
    candidates.append(Path.cwd() / "desafios" / "injestao-busca-semantica" / ".env")
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Arquivo .env não encontrado. Procurei em:\n  - "
        + "\n  - ".join(str(p) for p in candidates)
    )


def validate_env(
    env_path: str = ".env",
    context: str = "all",
    validate_paths: bool = True,
    script_file: Optional[str] = None,
) -> None:
    """
    Carrega e valida variáveis do .env.
    
    Args:
        env_path: Caminho do arquivo .env (usa resolução automática se script_file informado)
        context: "ingest" | "search" | "all" - quais variáveis exigir
        validate_paths: Se True, valida que PDF_PATH existe (para ingest)
        script_file: __file__ do script chamador (para achar .env no debugger)
    """
    if script_file and (env_path == ".env" or not Path(env_path).exists()):
        path = _resolve_env_path(script_file)
    else:
        path = Path(env_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo {env_path} não encontrado")
    load_dotenv(path)

    errors = []
    
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
            
        key = line.split("=", 1)[0].strip()
        if not key:
            continue
            
        raw_value = line.split("=", 1)[1].strip().strip("'\"").strip()
        
        # Valor vazio no arquivo (API keys de provedores são opcionais individualmente)
        if not raw_value:
            if key in ("GOOGLE_API_KEY", "OPENAI_API_KEY"):
                continue
            errors.append(f"'{key}' está vazia no {path}")
            continue
        
        # Valida no ambiente (após load_dotenv)
        env_value = os.getenv(key)
        if not env_value or not str(env_value).strip():
            errors.append(f"'{key}' não carregada no ambiente")
            continue
        
        # Validações específicas
        if key == "DATABASE_URL" and context in ("ingest", "search", "all"):
            if not (env_value.startswith("postgresql://") or env_value.startswith("postgresql+psycopg")):
                errors.append(f"'{key}' deve começar com postgresql:// ou postgresql+psycopg://")
        
        if key == "PDF_PATH" and validate_paths and context in ("ingest", "all"):
            if not Path(env_value).exists():
                errors.append(f"'{key}' aponta para arquivo inexistente: {env_value}")
    
    # Pelo menos uma API key (para ingest/search)
    if context in ("ingest", "search", "all"):
        if not (os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            errors.append("Configure OPENAI_API_KEY ou GOOGLE_API_KEY")
    
    if errors:
        raise RuntimeError("Erros de validação:\n" + "\n".join(f"  - {e}" for e in errors))