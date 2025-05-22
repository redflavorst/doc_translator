from pathlib import Path
import json
from typing import Dict, Any, Optional

from file_utils import convert_pdf_to_markdown
from translator import translate_paragraph
from progress_manager import progress_manager

DATA_DIR = Path('data')
CONVERTED_DIR = DATA_DIR / 'converted'
TRANSLATED_DIR = DATA_DIR / 'translated'
JSON_OUTPUT_DIR = DATA_DIR / 'json_output'


def ensure_directories():
    """Ensure all required directories exist."""
    for directory in [CONVERTED_DIR, TRANSLATED_DIR, JSON_OUTPUT_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def save_json(data: Dict[str, Any], file_path: Path) -> Path:
    """Save data as JSON file."""
    json_path = JSON_OUTPUT_DIR / f"{file_path.stem}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    return json_path


def extract_json_from_pdf_wrapper(file_path: Path) -> Optional[Dict[str, Any]]:
    """Extract JSON data from PDF."""
    try:
        # Try to get JSON data directly from extract_json_from_pdf if it exists
        if hasattr(extract_json_from_pdf, '__call__'):
            return extract_json_from_pdf(file_path)
        
        # Fallback to text extraction and create a simple JSON structure
        text = extract_text_from_pdf(file_path)
        return {
            'metadata': {
                'source': str(file_path.name),
                'pages': 1  # Default value, can be updated if page info is available
            },
            'content': [
                {
                    'type': 'text',
                    'text': text,
                    'page': 1
                }
            ]
        }
    except Exception as e:
        print(f"Error extracting JSON from PDF: {e}")
        return None


def run_translation(path: str, output_json: bool = True):
    """
    Run translation pipeline on a PDF file.
    
    Args:
        path: Path to the PDF file
        output_json: Whether to save JSON output
    """
    print(f'Processing file: {path}')
    file_path = Path(path)
    progress_manager.start(path)
    
    try:
        # Ensure all output directories exist
        ensure_directories()
        
        # 1. Extract text from PDF
        text = extract_text_from_pdf(file_path)
        
        # 2. Save extracted text as markdown
        converted_path = CONVERTED_DIR / (file_path.stem + '.md')
        converted_path.write_text(text, encoding='utf-8')
        print(f"Markdown saved to: {converted_path}")
        
        # 3. Extract JSON if requested
        json_data = None
        if output_json:
            json_data = extract_json_from_pdf_wrapper(file_path)
            if json_data:
                json_path = save_json(json_data, file_path)
                print(f"JSON data saved to: {json_path}")
        
        # 4. Translate the text
        translated = translate_paragraph(text)
        
        # 5. Save translated text
        translated_path = TRANSLATED_DIR / (file_path.stem + '.txt')
        translated_path.write_text(translated, encoding='utf-8')
        print(f"Translation saved to: {translated_path}")
        
        progress_manager.finish(path)
        return {
            'status': 'completed',
            'markdown_path': str(converted_path),
            'translated_path': str(translated_path),
            'json_path': str(JSON_OUTPUT_DIR / f"{file_path.stem}.json") if json_data else None
        }
        
    except Exception as e:
        error_msg = f"Error processing {path}: {str(e)}"
        print(error_msg)
        progress_manager.error(path, error_msg)
        return {'status': 'error', 'error': error_msg}
