from pathlib import Path
from langdetect import detect


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(file_path))
    except Exception:
        return ""


def scan_pdfs(folder_path: str):
    """Scan ``folder_path`` recursively and return info for all PDF files."""

    result = []
    for path in Path(folder_path).rglob("*.pdf"):
        text = extract_text_from_pdf(path)

        try:
            lang = detect(text)
        except Exception:
            lang = "unknown"

        result.append({"name": path.name, "path": str(path), "lang": lang})

    return result


# Backwards compatibility
scan_foreign_docs = scan_pdfs
