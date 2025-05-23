from pathlib import Path
import json
from typing import Dict, Any, Optional

from file_utils import convert_pdf_to_markdown
from translator import translate_paragraph, translate_markdown
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


def run_translation(path: str, output_json: bool = False):
    """
    Run translation pipeline on a PDF file.
    
    Args:
        path: Path to the PDF file
        output_json: Whether to save JSON output (기본값을 False로 변경)
    """
    print(f'Processing file: {path}')
    file_path = Path(path)
    progress_manager.start(path)
    
    try:
        # Ensure all output directories exist
        ensure_directories()
        
        # 1. 마크다운 파일 경로 확인 (PDF 파일명과 동일하지만 확장자가 .md)
        md_path = file_path.with_suffix('.md')
        
        # 마크다운 파일이 없으면 변환
        if not md_path.exists():
            print(f"마크다운 파일이 없어 변환을 시작합니다: {md_path}")
            md_path = convert_pdf_to_markdown(file_path)
        
        # 마크다운 파일 읽기
        with open(md_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 2. 변환된 마크다운 파일을 저장 디렉토리로 복사
        converted_path = CONVERTED_DIR / (file_path.stem + '.md')
        with open(converted_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Markdown saved to: {converted_path}")
        
        # 3. JSON 변환 비활성화 (필요없다고 하셨으므로)
        json_data = None
        
        # 4. Translate the text (마크다운 헤더 기준으로 분할하여 번역)
        # path 매개변수를 전달하여 진행 상황을 추적할 수 있게 함
        translated = translate_markdown(text, path)
        
        # 5. Save translated text
        translated_path = TRANSLATED_DIR / (file_path.stem + '.txt')
        translated_path.write_text(translated, encoding='utf-8')
        print(f"Translation saved to: {translated_path}")
        print(f"번역 완료: {file_path.name}")
        
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
