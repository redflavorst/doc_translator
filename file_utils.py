from pathlib import Path
from langdetect import detect


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(file_path))
    except Exception:
        return ""


def scan_foreign_docs(folder_path: str):
    result = []
    for path in Path(folder_path).rglob("*.pdf"):
        text = extract_text_from_pdf(path)
        try:
            lang = detect(text)
        except Exception:
            lang = 'unknown'
        if lang not in ('ko', 'unknown'):
            result.append({'name': path.name, 'path': str(path), 'lang': lang})
    return result
