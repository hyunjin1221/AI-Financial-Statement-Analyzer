from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.config import settings


def ensure_report_dir(output_dir: Optional[str] = None) -> Path:
    out_dir = Path(output_dir or settings.report_output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def save_markdown_report(markdown_text: str, ticker: str, filing_form: str, output_dir: Optional[str] = None) -> Path:
    out_dir = ensure_report_dir(output_dir=output_dir)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_ticker = "".join(ch for ch in ticker.upper() if ch.isalnum() or ch in {"_", "-"})
    safe_form = "".join(ch for ch in filing_form.upper() if ch.isalnum() or ch in {"_", "-"})
    filename = f"{safe_ticker}_{safe_form}_{timestamp}.md"
    path = out_dir / filename
    path.write_text(markdown_text, encoding="utf-8")
    return path


def list_recent_reports(limit: int = 10, output_dir: Optional[str] = None) -> List[Path]:
    out_dir = ensure_report_dir(output_dir=output_dir)
    files = sorted(out_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]
