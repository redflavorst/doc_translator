from pathlib import Path
import logging

from file_utils import convert_pdf_to_markdown  # PDF를 Markdown 문자열로 변환
from argos_translator import translate_markdown  # Markdown 문자열을 번역
from progress_manager import progress_manager

logger = logging.getLogger(__name__)

# New root directory for all processed files
DATA_ROOT_DIR = Path('data_translated')

def get_original_markdown_path(original_input_path_str: str) -> Path:
    """Gets the path for the stored original markdown file."""
    original_input_path = Path(original_input_path_str)
    file_stem = original_input_path.stem
    return DATA_ROOT_DIR / file_stem / (file_stem + '.md')

def get_translated_file_path(original_input_path_str: str) -> Path:
    """Gets the path for the translated markdown file."""
    original_input_path = Path(original_input_path_str)
    file_stem = original_input_path.stem
    return DATA_ROOT_DIR / file_stem / (file_stem + '_translated.md')

def run_translation(path: str):
    """
    Runs the translation pipeline for a given file (PDF or Markdown).
    The output will be structured under DATA_ROOT_DIR/filename_stem/
    with original as filename_stem.md and translation as filename_stem_translated.md.

    Args:
        path: Path string to the source file.
    """
    logger.info(f'Processing file: {path}')
    input_file_path = Path(path)
    file_stem = input_file_path.stem
    progress_manager.start(path)

    try:
        # 1. Define and create the output directory for the current file
        # e.g., data_translated/filename_stem/
        current_file_output_dir = DATA_ROOT_DIR / file_stem
        current_file_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory for this file: {current_file_output_dir}")

        # 2. Prepare original Markdown content and save it
        original_md_target_path = current_file_output_dir / (file_stem + '.md')
        markdown_content_for_translation: str

        if input_file_path.suffix.lower() == '.md':
            # If input is already Markdown, read its content
            markdown_content_for_translation = input_file_path.read_text(encoding='utf-8')
            # Save a copy to the new structured directory
            original_md_target_path.write_text(markdown_content_for_translation, encoding='utf-8')
            logger.info(f"Original Markdown copied to: {original_md_target_path}")
        elif input_file_path.suffix.lower() == '.pdf':
            # Convert PDF to Markdown content string
            markdown_content_for_translation = convert_pdf_to_markdown(input_file_path)
            
            if not markdown_content_for_translation:
                err_msg = f"Markdown conversion failed or returned empty content for {input_file_path}"
                logger.error(err_msg)
                raise Exception(err_msg)
            
            # Save the converted Markdown content to our target path
            original_md_target_path.write_text(markdown_content_for_translation, encoding='utf-8')
            logger.info(f"Converted Markdown from PDF saved to: {original_md_target_path}")
        else:
            unsupported_msg = f"File type {input_file_path.suffix} is not directly supported. Please provide a PDF or Markdown file."
            logger.error(unsupported_msg)
            progress_manager.error(path, unsupported_msg)
            # Return an error structure consistent with other returns
            return {'status': 'error', 'error': unsupported_msg} 

        # 3. Translate the Markdown content
        # translate_markdown should take the actual markdown string and return translated markdown string.
        # The 'path' argument is passed to translate_markdown for progress tracking within the translator.
        
        # 적응형 하이브리드 번역 모드 사용 (품질과 속도 균형)
        USE_ADAPTIVE_MODE = True  # True: 적응형 하이브리드, False: 문장별 고품질 모드
        
        if USE_ADAPTIVE_MODE:
            logger.info("적응형 하이브리드 번역 모드 사용 (문서 특성에 따라 자동 최적화)")
            translated_markdown_content = translate_markdown(markdown_content_for_translation, path)
        else:
            logger.info("문장별 고품질 번역 모드 사용")
            translated_markdown_content = translate_markdown(markdown_content_for_translation, path, use_sentence_mode=True)

        # 4. Save translated Markdown
        translated_md_path = current_file_output_dir / (file_stem + '_translated.md')
        translated_md_path.write_text(translated_markdown_content, encoding='utf-8')
        logger.info(f"Translated Markdown saved to: {translated_md_path}")
        logger.info(f"번역 완료: {input_file_path.name}")

        progress_manager.finish(path)
        return {
            'status': 'completed',
            'original_markdown_path': str(original_md_target_path),
            'translated_markdown_path': str(translated_md_path),
        }

    except Exception as e:
        error_msg = f"Error processing {path}: {str(e)}"
        logger.exception(f"Exception in run_translation for {path}") # Log with stack trace
        progress_manager.error(path, error_msg)
        return {'status': 'error', 'error': error_msg}
