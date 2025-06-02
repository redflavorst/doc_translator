from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import re
import os
import tempfile
import logging
from enum import Enum, auto

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileType(Enum):
    PDF = auto()
    TEXT = auto()
    MARKDOWN = auto()
    UNSUPPORTED = auto()

# 언어 감지 모듈은 필요할 때만 임포트
langdetect_imported = False
try:
    from langdetect import detect, detect_langs
    from langdetect.lang_detect_exception import LangDetectException
    langdetect_imported = True
except ImportError:
    langdetect_imported = False
    logger.warning("langdetect 모듈을 찾을 수 없습니다. 언어 감지 기능이 제한됩니다.")

# PyMuPDF를 선택적으로 임포트
fitz_imported = False
try:
    import fitz  # PyMuPDF
    fitz_imported = True
except ImportError:
    fitz_imported = False
    logger.warning("PyMuPDF 모듈을 찾을 수 없습니다. PDF 텍스트 추출 기능이 제한됩니다.")

# docling 모듈은 필요할 때만 임포트
docling_imported = False
if not docling_imported:
    try:
        from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        docling_imported = True
    except ImportError:
        logger.warning("docling 모듈이 설치되지 않았습니다. 일부 PDF 처리 기능이 제한됩니다.")


def get_file_type(file_path: Path) -> FileType:
    """
    파일 경로를 기반으로 파일 유형을 반환합니다.
    
    Args:
        file_path (Path): 파일 경로
        
    Returns:
        FileType: 파일 유형 (PDF, TEXT, MARKDOWN, UNSUPPORTED)
    """
    ext = file_path.suffix.lower()
    if ext == '.pdf':
        return FileType.PDF
    elif ext in ['.txt']:
        return FileType.TEXT
    elif ext in ['.md', '.markdown']:
        return FileType.MARKDOWN
    else:
        return FileType.UNSUPPORTED

def extract_text_from_pdf(file_path: Path, max_pages: int = 20) -> str:
    """
    PDF 파일에서 텍스트를 추출합니다. PyMuPDF를 먼저 시도하고 실패하면 PyPDF2를 사용합니다.
    
    Args:
        file_path: PDF 파일 경로
        max_pages: 처리할 최대 페이지 수
        
    Returns:
        str: 추출된 텍스트
    """
    text = ""
    
    # 1. PyMuPDF로 시도 (더 안정적)
    if fitz_imported:
        try:
            doc = fitz.open(file_path)
            for i, page in enumerate(doc):
                if i >= max_pages:
                    break
                page_text = page.get_text()
                if page_text.strip():
                    text += page_text + "\n"
            doc.close()
            if text.strip():
                logger.info(f"PyMuPDF로 텍스트 추출 성공: {len(text)}자")
                return text
        except Exception as e:
            logger.warning(f"PyMuPDF 추출 실패: {e}")
    else:
        logger.warning("PyMuPDF가 설치되어 있지 않아 PyPDF2로 대체합니다.")
    
    # 2. PyPDF2로 백업 시도
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for i in range(min(max_pages, len(reader.pages))):
                try:
                    page_text = reader.pages[i].extract_text() or ""
                    text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"PDF 페이지 {i+1}에서 텍스트 추출 중 오류: {e}")
        
        if text.strip():
            logger.info(f"PyPDF2로 텍스트 추출 성공: {len(text)}자")
            return text
    except Exception as e:
        logger.error(f"PyPDF2 추출 실패: {e}")
    
    return text

def analyze_character_distribution(text: str) -> Dict[str, float]:
    """
    텍스트의 문자 분포를 분석하여 언어별 점수를 계산합니다.
    
    Args:
        text: 분석할 텍스트
        
    Returns:
        Dict[str, float]: 언어 코드를 키로, 점수를 값으로 하는 딕셔너리
    """
    if not text or len(text) < 10:
        return {}
    
    total_chars = len(text)
    scores = {}
    
    # 일본어 패턴
    hiragana = len(re.findall(r'[\u3040-\u309F]', text))  # 히라가나
    katakana = len(re.findall(r'[\u30A0-\u30FF]', text))  # 가타카나
    kanji = len(re.findall(r'[\u4E00-\u9FAF]', text))     # 한자
    
    # 일본어 점수 (히라가나에 가중치 부여)
    japanese_score = (hiragana * 3 + katakana * 2 + kanji) / total_chars
    if hiragana > 0:
        japanese_score *= 2
    scores['ja'] = japanese_score
    
    # 한국어 패턴
    hangul = len(re.findall(r'[\uAC00-\uD7AF]', text))  # 한글
    korean_score = hangul / total_chars
    scores['ko'] = korean_score
    
    # 중국어 점수 (한자만 있고 히라가나/한글이 없을 때)
    chinese_score = kanji / total_chars if hiragana == 0 and hangul == 0 else 0
    scores['zh'] = chinese_score
    
    # 영어 점수
    english = len(re.findall(r'[a-zA-Z]', text))
    scores['en'] = english / total_chars
    
    return scores

def detect_language_enhanced(text: str) -> Tuple[str, float]:
    """
    향상된 언어 감지 함수로, 여러 방법을 조합하여 더 정확한 언어 감지를 수행합니다.
    
    Args:
        text: 감지할 텍스트
        
    Returns:
        Tuple[str, float]: (언어 코드, 신뢰도)
    """
    if not text or len(text.strip()) < 10:
        return 'en', 0.0
    
    # 1. 문자 분포 분석
    char_scores = analyze_character_distribution(text)
    
    # 2. langdetect 사용
    langdetect_result = None
    if langdetect_imported:
        try:
            clean_text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\uAC00-\uD7AF]', ' ', text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            if len(clean_text) >= 10:
                detected_lang = detect(clean_text)
                confidence = 0.9  # 기본 신뢰도
                
                # langdetect의 신뢰도 점수 가져오기
                try:
                    langs = detect_langs(clean_text)
                    if langs:
                        confidence = langs[0].prob
                except:
                    pass
                
                langdetect_result = (detected_lang, confidence)
        except Exception as e:
            logger.warning(f"langdetect 오류: {e}")
    
    # 3. 키워드 기반 분석
    keyword_scores = {}
    japanese_keywords = ['契約', '条項', '甲', '乙', '丙', '賃貸借', '機器', '設置']
    korean_keywords = ['계약', '조항', '임대차', '기기', '설치']
    
    for keyword in japanese_keywords:
        if keyword in text:
            keyword_scores['ja'] = keyword_scores.get('ja', 0) + 1
    
    for keyword in korean_keywords:
        if keyword in text:
            keyword_scores['ko'] = keyword_scores.get('ko', 0) + 1
    
    # 4. 최종 점수 계산
    scores = {}
    
    # 문자 분포 점수 (가중치 3)
    for lang, score in char_scores.items():
        if score > 0.1:  # 임계값 이상만 고려
            scores[lang] = scores.get(lang, 0) + score * 3
    
    # langdetect 점수 (가중치 2)
    if langdetect_result:
        lang, confidence = langdetect_result
        if confidence > 0.7:  # 신뢰도가 높을 때만 고려
            scores[lang] = scores.get(lang, 0) + confidence * 2
    
    # 키워드 점수 (가중치 1)
    for lang, count in keyword_scores.items():
        scores[lang] = scores.get(lang, 0) + count
    
    # 가장 높은 점수의 언어 반환
    if scores:
        best_lang = max(scores.items(), key=lambda x: x[1])
        total = sum(scores.values())
        confidence = best_lang[1] / total if total > 0 else 0
        return best_lang[0], confidence
    
    return 'en', 0.0  # 기본값

def extract_text_from_file(file_path: Path, max_chars: int = 5000) -> str:
    """
    파일에서 텍스트를 추출합니다.
    
    이 함수는 PDF, 텍스트, 마크다운 파일에서 텍스트를 추출합니다.
    성능을 위해 기본적으로 처음 5000자만 추출합니다.
    
    Args:
        file_path (Path): 텍스트를 추출할 파일 경로
        max_chars (int, optional): 추출할 최대 문자 수. 기본값은 5000자.
        
    Returns:
        str: 추출된 텍스트. 오류 발생 시 빈 문자열을 반환합니다.
    """
    if not file_path or not file_path.exists() or not file_path.is_file():
        logger.warning(f"파일이 존재하지 않거나 유효하지 않습니다: {file_path}")
        return ""
    
    # 파일 크기 확인 (100MB 제한)
    try:
        file_size = file_path.stat().st_size
        if file_size > 100 * 1024 * 1024:  # 100MB
            logger.warning(f"파일이 너무 커서 텍스트 추출을 건너뜁니다: {file_path}")
            return ""
    except Exception as e:
        logger.warning(f"파일 크기 확인 중 오류 발생 ({file_path}): {e}")
    
    try:
        file_type = get_file_type(file_path)
        text = ""
        
        if file_type == FileType.PDF:
            # PDF에서 텍스트 추출
            text = extract_text_from_pdf(file_path)
            
            # 텍스트가 너무 적으면 경고 로그
            if len(text.strip()) < 100:
                logger.warning(f"PDF에서 추출된 텍스트가 매우 적습니다: {len(text.strip())}자")
                
        elif file_type in [FileType.TEXT, FileType.MARKDOWN]:
            # 텍스트 파일에서 읽기 (여러 인코딩 시도)
            encodings = ['utf-8', 'cp949', 'euc-kr', 'iso-8859-1', 'latin1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        text = f.read(max_chars * 2)  # 약간의 여유를 두고 읽기
                    break  # 성공하면 루프 종료
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"파일 읽기 중 오류 발생 (인코딩: {encoding}): {e}")
                    continue
            else:
                logger.error(f"지원되는 인코딩으로 파일을 읽을 수 없습니다: {file_path}")
        else:
            logger.warning(f"지원되지 않는 파일 형식입니다: {file_path}")
        
        # 텍스트 전처리
        if text:
            # 연속된 공백과 개행 정리
            text = ' '.join(text.split())
            # 최대 길이 제한
            text = text[:max_chars]
            
        return text
        
    except Exception as e:
        logger.error(f"파일에서 텍스트 추출 중 치명적 오류 발생 ({file_path}): {e}", exc_info=True)
        return ""

def normalize_lang_code(lang_code: str) -> str:
    """
    언어 코드를 2자리 코드로 정규화합니다.
    
    Args:
        lang_code (str): 정규화할 언어 코드 (예: 'zh-cn', 'en-US')
        
    Returns:
        str: 2자리 언어 코드 (예: 'zh', 'en')
    """
    if not lang_code:
        return 'en'
    
    # 하이픈이나 언더스코어로 분리하여 첫 부분만 사용
    base_code = lang_code.split('-')[0].split('_')[0].lower()
    
    # 2자리로 제한
    return base_code[:2] if len(base_code) >= 2 else base_code


def detect_document_language(file_path: Path, sample_size: int = 5000) -> Tuple[str, float]:
    """
    문서 파일의 언어를 감지합니다.
    
    이 함수는 파일에서 텍스트를 추출하고, 텍스트의 언어를 자동으로 감지합니다.
    신뢰도 점수도 함께 반환하여 언어 감지의 정확도를 나타냅니다.
    
    Args:
        file_path (Path): 감지할 파일 경로
        sample_size (int): 언어 감지에 사용할 샘플 크기(문자 수). 
                         성능을 위해 기본값은 5000자로 제한됩니다.
        
    Returns:
        Tuple[str, float]: (감지된 언어 코드, 신뢰도 0.0~1.0). 
                         감지 실패 시 ('en', 0.0)을 반환합니다.
                         
    Examples:
        >>> detect_document_language(Path("document.pdf"))
        ('ko', 0.98)
        
        >>> detect_document_language(Path("document.txt"), sample_size=10000)
        ('en', 0.95)
    """
    if not langdetect_imported:
        logger.warning("langdetect 모듈이 없어 언어 감지를 수행할 수 없습니다.")
        return 'en', 0.0
    
    # 파일 크기 확인 (100MB 제한)
    try:
        file_size = file_path.stat().st_size
        if file_size > 100 * 1024 * 1024:  # 100MB
            logger.warning(f"파일이 너무 커서 언어 감지를 건너뜁니다: {file_path}")
            return 'en', 0.0
    except Exception as e:
        logger.warning(f"파일 크기 확인 중 오류 발생 ({file_path}): {e}")
    
    try:
        # 1. 파일에서 텍스트 추출 (성능을 위해 샘플 크기 제한)
        text = extract_text_from_file(file_path, sample_size)
        
        # 2. 텍스트가 비어있는지 확인
        if not text or not text.strip():
            logger.warning(f"추출된 텍스트가 없습니다: {file_path}")
            return 'en', 0.0
        
        # 3. 텍스트가 너무 짧으면 신뢰도가 낮을 수 있음
        if len(text) < 20:  # 20자 미만이면 신뢰도 낮게 설정
            logger.warning(f"텍스트가 너무 짧아 정확한 언어 감지가 어렵습니다: {file_path}")
            return 'en', 0.1
            
        # 4. 언어 감지 (여러 알고리즘 조합)
        from langdetect import detect_langs, DetectorFactory
        
        # 재현성을 위한 시드 설정
        DetectorFactory.seed = 0
        
        try:
            # 4.1. 전체 텍스트로 먼저 시도
            langs = detect_langs(text)
            
            if not langs:
                logger.warning(f"언어를 감지할 수 없습니다: {file_path}")
                return 'en', 0.0
                
            # 4.2. 신뢰도가 가장 높은 언어 선택
            best_match = max(langs, key=lambda x: x.prob)
            
            # 4.3. 신뢰도가 너무 낮으면 추가 검증 수행
            if best_match.prob < 0.7:  # 70% 미만이면
                # 텍스트를 여러 부분으로 나누어 일관성 확인
                chunks = [text[i:i+1000] for i in range(0, min(3000, len(text)), 1000)]
                if len(chunks) > 1:
                    chunk_langs = []
                    for chunk in chunks:
                        try:
                            chunk_lang = detect_langs(chunk)
                            if chunk_lang:
                                chunk_langs.append(chunk_lang[0].lang)
                        except:
                            continue
                    
                    # 모든 청크에서 동일한 언어가 감지되었는지 확인
                    if chunk_langs and all(lang == best_match.lang for lang in chunk_langs):
                        # 일관된 언어 감지 시 신뢰도 향상
                        best_match.prob = min(1.0, best_match.prob + 0.2)
            
            # 언어 코드 정규화 (예: 'zh-cn' -> 'zh')
            normalized_lang = normalize_lang_code(best_match.lang)
            logger.info(f"언어 감지 완료: {file_path} -> {normalized_lang} (원본: {best_match.lang}, 신뢰도: {best_match.prob:.2f})")
            return normalized_lang, best_match.prob
            
        except Exception as e:
            logger.warning(f"고급 언어 감지 중 오류 발생 ({file_path}): {e}")
            
            # 간단한 감지로 폴백
            try:
                lang = detect(text)
                normalized_lang = normalize_lang_code(lang)
                logger.info(f"간단한 언어 감지 완료: {file_path} -> {normalized_lang} (원본: {lang}, 신뢰도: 0.9)")
                return normalized_lang, 0.9  # 간단한 감지는 신뢰도 0.9로 가정
            except:
                logger.error(f"간단한 언어 감지도 실패: {file_path}")
                return 'en', 0.0
            
    except Exception as e:
        logger.error(f"언어 감지 중 치명적 오류 발생 ({file_path}): {e}", exc_info=True)
        return 'en', 0.0

def convert_pdf_to_markdown(pdf_path: Path, use_ocr: bool = False) -> str:
    """
    PDF 파일을 마크다운(.md) 파일로 변환하여 저장합니다.
    
    이 함수는 PDF 파일을 마크다운 형식으로 변환합니다. 
    OCR을 사용하여 이미지 기반 PDF도 처리할 수 있습니다.
    
    Args:
        pdf_path (Path): 변환할 PDF 파일 경로
        use_ocr (bool, optional): 이미지 기반 PDF의 경우 OCR 사용 여부. 
                                기본값은 False입니다.
                                
    Returns:
        str: 변환된 마크다운 콘텐츠
        
    Raises:
        FileNotFoundError: PDF 파일을 찾을 수 없는 경우
        RuntimeError: 변환 과정에서 오류가 발생한 경우
        
    Examples:
        >>> markdown_content = convert_pdf_to_markdown(Path("document.pdf"))
        >>> # markdown_content는 이제 문자열입니다.
        
        >>> markdown_content_ocr = convert_pdf_to_markdown(Path("scanned.pdf"), use_ocr=True)
        >>> # markdown_content_ocr는 이제 문자열입니다.
    """
    # 1. 입력 유효성 검사
    pdf_path = Path(pdf_path).resolve()
    if not pdf_path.exists() or not pdf_path.is_file():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    
    # 2. docling 모듈 로드 확인
    if not docling_imported:
        raise ImportError("PDF 변환을 위해서는 docling 패키지가 필요합니다. 'pip install docling'으로 설치해주세요.")
    
    logger.info(f"PDF → Markdown 변환 시작: {pdf_path}")
    logger.info(f"OCR 사용: {'예' if use_ocr else '아니오'}")
    
    try:
        # 5. PDF 파이프라인 옵션 설정
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
        
        pipeline_options = PdfPipelineOptions()
        
        # OCR 설정 수정 (기존 에러 부분)
        if use_ocr:
            ocr_options = TesseractCliOcrOptions(lang=["auto"])
            pipeline_options.do_ocr = True
            pipeline_options.force_full_page_ocr = True
            pipeline_options.ocr_options = ocr_options
        else:
            pipeline_options.do_ocr = False
            
        pipeline_options.do_table_structure = True  # 표 구조 인식 활성화
        
        pdf_options = PdfFormatOption(pipeline_options=pipeline_options)
        
        # 6. DocumentConverter 생성 및 변환 수행
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: pdf_options
            }
        )
        
        # 7. 변환 실행
        result = converter.convert(str(pdf_path))
        
        # 8. 변환 결과 검증
        if not hasattr(result, 'document') or not hasattr(result.document, 'export_to_markdown'):
            raise RuntimeError("변환 결과에서 마크다운을 추출할 수 없습니다. PDF 형식을 확인해주세요.")
        
        # 9. 마크다운 내보내기
        markdown_content = result.document.export_to_markdown()
        
        # 10. 변환된 마크다운 콘텐츠 반환
        logger.info(f"PDF → Markdown 변환 완료: {pdf_path} (콘텐츠 길이: {len(markdown_content)})")
        return markdown_content
        
    except Exception as e:
        error_msg = f"PDF → Markdown 변환 실패: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        raise RuntimeError(error_msg) from e


def scan_pdfs(folder_path: str) -> List[Dict[str, Any]]:
    """
    폴더를 재귀적으로 스캔하여 PDF 파일 정보를 반환합니다.
    
    Args:
        folder_path (str): 스캔할 폴더 경로
        
    Returns:
        List[Dict[str, Any]]: 파일 정보가 담긴 딕셔너리 리스트
    """
    if not folder_path or not os.path.isdir(folder_path):
        return []
    
    pdf_files = []
    supported_extensions = ['.pdf', '.txt', '.md', '.markdown']
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext not in supported_extensions:
                continue
                
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                
                # 1KB 미만 파일은 건너뜀
                if file_size < 1024:
                    continue
                    
                # 100MB 초과 파일은 건너뜀
                if file_size > 100 * 1024 * 1024:
                    logger.warning(f"파일 크기가 너무 커서 건너뜁니다 (100MB 초과): {file_path}")
                    continue
                
                # 파일 유형 결정
                file_type = get_file_type(Path(file_path))
                if file_type == FileType.UNSUPPORTED:
                    continue
                
                # 언어 감지 (성능을 위해 샘플 텍스트 사용)
                lang, confidence = detect_document_language(Path(file_path))
                
                # 파일 정보 수집
                file_info = {
                    'name': file,
                    'path': file_path,
                    'size': file_size,
                    'type': file_ext[1:],  # 확장자에서 점 제거
                    'status': 'pending',
                    'language': lang,
                    'confidence': round(confidence * 100, 1),  # 백분율로 변환
                    'last_modified': os.path.getmtime(file_path)
                }
                
                # PDF인 경우 추가 정보 수집
                if file_type == FileType.PDF:
                    try:
                        import PyPDF2
                        with open(file_path, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            file_info['pages'] = len(reader.pages)
                    except Exception as e:
                        logger.warning(f"PDF 페이지 수 확인 중 오류 발생 ({file_path}): {e}")
                        file_info['pages'] = 0
                
                pdf_files.append(file_info)
                
            except Exception as e:
                logger.error(f"파일 처리 중 오류 발생 ({file_path}): {e}")
    
    # 파일 크기 내림차순 정렬 (큰 파일이 먼저 오도록)
    pdf_files.sort(key=lambda x: x['size'], reverse=True)
    
    return pdf_files


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
