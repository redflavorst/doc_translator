from pathlib import Path
from typing import Optional, Dict, Any
from langdetect import detect
from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling.datamodel.pipeline_options import PdfPipelineOptions
import tempfile
import shutil
import os
import json
from datetime import datetime


def convert_pdf_to_markdown(pdf_path: Path, output_dir: Path = None, use_ocr: bool = False) -> str:
    """
    PDF 파일을 마크다운(.md) 파일로 변환하여 저장합니다.

    Args:
        pdf_path (Path): 변환할 PDF 파일 경로
        output_dir (Path, optional): 마크다운 파일 저장 디렉토리. None이면 PDF와 같은 위치에 저장
        use_ocr (bool): 이미지 기반 PDF의 경우 OCR 사용 여부
    Returns:
        str: 저장된 마크다운 파일 경로
    """
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = pdf_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{pdf_path.stem}.md"

    # PDF 파이프라인 옵션 설정
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = use_ocr
    pipeline_options.do_table_structure = True
    pdf_options = PdfFormatOption(pipeline_options=pipeline_options)

    # DocumentConverter 생성
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: pdf_options
        }
    )

    print(f"PDF → Markdown 변환 시작: {pdf_path}")
    try:
        result = converter.convert(str(pdf_path))
        if not hasattr(result, 'document') or not hasattr(result.document, 'export_to_markdown'):
            raise RuntimeError("Docling 변환 결과에서 마크다운을 추출할 수 없습니다.")
        markdown_content = result.document.export_to_markdown()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"변환 완료: {output_path}")
        return str(output_path)
    except Exception as e:
        print(f"PDF → Markdown 변환 실패: {e}")
        raise


def scan_pdfs(folder_path: str) -> list:
    """
    Scan a folder recursively and return info for all PDF files.
    
    Args:
        folder_path: Path to the folder to scan
        
    Returns:
        list: List of dictionaries containing file info
    """
    result = []
    for path in Path(folder_path).rglob("*.pdf"):
        # Extract a small portion of text for language detection
        try:
            with open(path, 'rb') as f:
                # Read only first 100KB for language detection
                text = f.read(102400).decode('utf-8', errors='ignore')
                
            lang = detect(text) if text.strip() else "unknown"
            
            result.append({
                "name": path.name,
                "path": str(path),
                "lang": lang,
                "size": path.stat().st_size,
                "mtime": path.stat().st_mtime
            })
            
        except Exception as e:
            print(f"Error processing {path}: {e}")
            continue
            
    return result


def extract_json_from_pdf(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract structured data from PDF as JSON.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        dict: Extracted data in JSON format
    """
    try:
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            output_dir = temp_dir_path / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize Docling converter
            converter = DocumentConverter()
            
            # Convert PDF to JSON
            result = converter.convert(
                input_path=str(file_path),
                output_dir=str(output_dir),
                output_format="json",
                include_images=False
            )
            
            # If result is already a dictionary, return it
            if isinstance(result, dict):
                return _process_json_result(result, file_path)
                
            # If result is a path to a JSON file
            elif isinstance(result, (str, Path)):
                result_path = Path(result)
                if result_path.exists() and result_path.suffix.lower() == '.json':
                    with open(result_path, 'r', encoding='utf-8') as f:
                        return _process_json_result(json.load(f), file_path)
            
            # Fallback: look for JSON files in the output directory
            json_files = list(output_dir.rglob("*.json"))
            if json_files:
                with open(json_files[0], 'r', encoding='utf-8') as f:
                    return _process_json_result(json.load(f), file_path)
                    
            raise FileNotFoundError("No JSON content was generated")
            
    except Exception as e:
        print(f"Error converting PDF to JSON: {e}")
        return None


def _process_json_result(data: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
    """Process and enhance the JSON result with additional metadata."""
    # Add metadata
    if 'metadata' not in data:
        data['metadata'] = {}
    
    data['metadata'].update({
        'source_file': str(file_path.name),
        'extraction_time': datetime.now().isoformat(),
        'file_size': file_path.stat().st_size,
        'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
    })
    
    # Ensure required fields exist
    if 'pages' not in data:
        if 'content' in data and isinstance(data['content'], str):
            # If we have plain text content, wrap it in a page structure
            data['pages'] = [{
                'page_number': 1,
                'content': data['content']
            }]
            del data['content']
        else:
            data['pages'] = []
    
    return data


# Backwards compatibility
scan_foreign_docs = scan_pdfs
