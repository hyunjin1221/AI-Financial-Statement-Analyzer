import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    sec_user_agent: str = os.getenv("SEC_USER_AGENT", "YourName your_email@example.com")
    sec_rate_limit_per_sec: float = float(os.getenv("SEC_RATE_LIMIT_PER_SEC", "5.0"))
    sec_timeout_seconds: int = int(os.getenv("SEC_TIMEOUT_SECONDS", "20"))
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    ollama_timeout_seconds: int = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "90"))
    llm_max_section_chars: int = int(os.getenv("LLM_MAX_SECTION_CHARS", "12000"))
    peer_max_workers: int = int(os.getenv("PEER_MAX_WORKERS", "4"))
    report_output_dir: str = os.getenv("REPORT_OUTPUT_DIR", "data/processed/reports")


settings = Settings()
