from pathlib import Path

from file_utils import extract_text_from_pdf
from translator import translate_paragraph
from progress_manager import progress_manager

DATA_DIR = Path('data')
CONVERTED_DIR = DATA_DIR / 'converted'
TRANSLATED_DIR = DATA_DIR / 'translated'


def run_translation(path: str):
    file_path = Path(path)
    progress_manager.start(path)

    text = extract_text_from_pdf(file_path)
    translated = translate_paragraph(text)

    converted_path = CONVERTED_DIR / (file_path.stem + '.md')
    converted_path.write_text(text, encoding='utf-8')

    translated_path = TRANSLATED_DIR / (file_path.stem + '.txt')
    translated_path.write_text(translated, encoding='utf-8')

    progress_manager.finish(path)
