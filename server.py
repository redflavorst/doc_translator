from flask import Flask, jsonify, request, send_from_directory, render_template
import threading
import base64
import os
import logging
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import subprocess
import time
import requests
import atexit

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 필요한 모듈은 나중에 임포트 (지연 로딩)
Pdf2ImageAvailable = False
PillowAvailable = False
langdetect_available = False

# 로컬 모듈 임포트
import file_utils
import tasks
from tasks import get_translated_file_path # Import the new helper function

app = Flask(__name__, static_folder='static', template_folder='templates')

# 서비스 초기화 플래그
_services_initialized = False

def initialize_services():
    """무거운 서비스 초기화를 지연로딩"""
    global Pdf2ImageAvailable, PillowAvailable, langdetect_available, _services_initialized
    
    if _services_initialized:
        return
        
    try:
        # pdf2image 초기화
        global convert_from_path, pdfinfo_from_path
        from pdf2image import convert_from_path, pdfinfo_from_path
        Pdf2ImageAvailable = True
        logger.info("pdf2image 모듈을 성공적으로 로드했습니다.")
    except ImportError:
        logger.warning("pdf2image 모듈을 로드할 수 없습니다. PDF 미리보기 기능이 제한됩니다.")
    
    try:
        # Pillow 초기화
        global Image, ImageEnhance
        from PIL import Image, ImageEnhance
        PillowAvailable = True
        logger.info("Pillow 모듈을 성공적으로 로드했습니다.")
    except ImportError:
        logger.warning("Pillow 모듈을 로드할 수 없습니다. 이미지 처리 기능이 제한됩니다.")
    
    try:
        # langdetect 초기화
        global detect, detect_langs, DetectorFactory
        from langdetect import detect, detect_langs, DetectorFactory
        from langdetect.lang_detect_exception import LangDetectException
        DetectorFactory.seed = 0  # 재현성을 위한 시드 설정
        langdetect_available = True
        logger.info("langdetect 모듈을 성공적으로 로드했습니다.")
    except ImportError:
        logger.warning("langdetect 모듈을 로드할 수 없습니다. 언어 감지 기능이 제한됩니다.")
    
    _services_initialized = True

# 서버 시작 시 서비스 초기화
if not _services_initialized:
    initialize_services()
    _services_initialized = True

@app.route('/')
def index():
    return render_template('index.html')

def is_foreign_language(text: str, threshold: float = 0.5) -> bool:
    """
    텍스트가 외국어(한국어가 아닌 언어)인지 확인합니다.
    
    Args:
        text: 분석할 텍스트
        threshold: 언어 감지 신뢰도 임계값 (0.0 ~ 1.0)
        
    Returns:
        bool: 한국어가 아니면 True, 한국어이거나 감지 실패 시 False
    """
    if not text.strip():
        return False
        
    try:
        if not langdetect_available:
            return False
            
        langs = detect_langs(text)
        if not langs:
            return False
            
        # 가장 신뢰도가 높은 언어 감지 결과 사용
        best_match = max(langs, key=lambda x: x.prob)
        
        # 한국어가 아니고 신뢰도가 threshold 이상인 경우 외국어로 판단
        return best_match.lang != 'ko' and best_match.prob >= threshold
        
    except Exception as e:
        logger.warning(f"언어 감지 중 오류: {e}")
        return False

def scan_directory_for_foreign_docs(directory: Path) -> List[Dict[str, Any]]:
    """
    디렉토리에서 문서를 스캔하여 모든 문서의 정보를 반환합니다.
    
    Args:
        directory: 스캔할 디렉토리 경로
        
    Returns:
        List[Dict]: 문서 정보 리스트 (한국어, 외국어 모두 포함)
    """
    if not directory.exists() or not directory.is_dir():
        logger.warning(f"디렉토리가 존재하지 않거나 유효하지 않습니다: {directory}")
        return []
    
    supported_extensions = {'.pdf', '.txt', '.md', '.markdown'}
    all_docs = []
    processed_files = set()  # 중복 처리 방지를 위한 집합
    
    # 디렉토리 내의 모든 파일을 재귀적으로 검색
    for file_path in directory.rglob('*'):
        try:
            # 디렉토리이거나 지원하지 않는 확장자인 경우 건너뜀
            if not file_path.is_file() or file_path.suffix.lower() not in supported_extensions:
                continue
                
            # 이미 처리한 파일인지 확인
            if str(file_path) in processed_files:
                continue
                
            # 파일 크기가 너무 작으면 건너뜀 (최소 1KB)
            file_size = file_path.stat().st_size
            if file_size < 1024:
                logger.debug(f"파일이 너무 작아 건너뜁니다: {file_path} ({file_size} bytes)")
                continue
                
            try:
                # 언어 감지
                logger.info(f"문서 처리 중: {file_path}")
                lang, confidence = file_utils.detect_document_language(file_path)
                
                # 파일 정보 생성 (모든 문서 포함)
                file_info = {
                    'name': file_path.name,  # 원본 파일명
                    'display_name': file_path.name,  # 표시용 파일명 (원본과 동일)
                    'path': str(file_path),
                    'size': file_size,
                    'language': lang,  # 언어 코드 (예: 'ko', 'en', 'ja')
                    'language_name': lang.upper() if lang else 'Unknown',  # 언어 코드 대문자
                    'confidence': round(confidence * 100, 1) if confidence else 0,  # 백분율로 변환
                    'is_foreign': lang != 'ko' and confidence and confidence >= 0.5  # 한국어가 아닌지 여부
                }
                
                all_docs.append(file_info)
                logger.info(f"문서 처리 완료: {file_path} -> {lang} (신뢰도: {confidence or 0:.2f}, 외국어: {file_info['is_foreign']})")
                
                # 처리된 파일로 표시
                processed_files.add(str(file_path))
                    
            except Exception as detect_error:
                logger.error(f"문서 처리 중 오류 발생 ({file_path}): {detect_error}", exc_info=True)
                
                # 오류 발생 시 기본 정보만 포함
                file_info = {
                    'name': file_path.name,
                    'display_name': file_path.name,
                    'path': str(file_path),
                    'size': file_size,
                    'language': 'unknown',
                    'language_name': 'Unknown',
                    'confidence': 0,
                    'is_foreign': False,
                    'error': str(detect_error)
                }
                all_docs.append(file_info)
                
        except Exception as e:
            logger.error(f"파일 처리 중 오류 발생 ({file_path}): {e}", exc_info=True)
    
    logger.info(f"총 {len(all_docs)}개의 문서를 찾았습니다.")
    return all_docs

def normalize_path(path_str: str) -> Path:
    """
    경로 문자열을 정규화하고 Path 객체로 변환합니다.
    백슬래시를 슬래시로 변환하고, 상대 경로를 절대 경로로 변환합니다.
    """
    if not path_str:
        return None
        
    # 백슬래시를 슬래시로 변환하고, 중복 슬래시 제거
    normalized = path_str.replace('\\', '/').replace('//', '/')
    
    # 경로 정규화 (상대 경로 해결, . 및 .. 처리)
    path_obj = Path(normalized).resolve()
    
    return path_obj

@app.route('/api/select-folder', methods=['POST'])
def select_folder():
    """
    폴더를 선택하고 한국어를 제외한 외국어 문서 목록을 반환합니다.
    
    요청 본문:
        {
            "path": "스캔할 폴더 경로"
        }
        
    응답:
        성공 시:
            {
                "success": true,
                "files": [
                    {
                        "name": "파일명.확장자",
                        "display_name": "표시용_파일명",
                        "path": "전체_파일_경로",
                        "size": 파일_크기_바이트,
                        "language": "언어_코드",
                        "language_name": "언어_이름",
                        "confidence": 신뢰도_0_100
                    },
                    ...
                ],
                "count": 문서_수
            }
        실패 시:
            {
                "success": false,
                "error": "오류_메시지"
            }
    """
    print("\n=== select_folder 함수 호출됨 ===")
    logger.info("새로운 폴더 선택 요청 수신")
    
    try:
        # 요청 데이터 검증
        logger.debug(f"요청 헤더: {dict(request.headers)}")
        logger.debug(f"요청 본문(raw): {request.get_data()}")
        
        if not request.is_json:
            error_msg = "잘못된 요청 형식: JSON이 아닙니다."
            logger.error(error_msg)
            return jsonify({'success': False, 'error': '요청은 JSON 형식이어야 합니다.'}), 400
            
        data = request.get_json()
        logger.debug(f"파싱된 JSON 데이터: {data}")
        
        folder_path = data.get('path')
        logger.info(f"원본 폴더 경로: {folder_path}")
        
        # 필수 파라미터 검증
        if not folder_path:
            error_msg = "필수 파라미터가 누락되었습니다: path"
            logger.error(error_msg)
            return jsonify({'success': False, 'error': '폴더 경로가 지정되지 않았습니다.'}), 400
        
        # 경로 정규화
        try:
            folder_path_obj = normalize_path(folder_path)
            if not folder_path_obj:
                raise ValueError("경로 정규화 실패")
                
            logger.info(f"정규화된 폴더 경로: {folder_path_obj}")
            
            # 존재 여부 확인
            if not folder_path_obj.exists():
                error_msg = f"존재하지 않는 폴더 경로: {folder_path_obj}"
                logger.error(error_msg)
                return jsonify({
                    'success': False, 
                    'error': '지정된 폴더가 존재하지 않습니다.',
                    'original_path': folder_path,
                    'normalized_path': str(folder_path_obj)
                }), 400
                
            if not folder_path_obj.is_dir():
                error_msg = f"폴더가 아닌 경로가 지정됨: {folder_path_obj}"
                logger.error(error_msg)
                return jsonify({
                    'success': False, 
                    'error': '유효한 폴더 경로가 아닙니다.',
                    'original_path': folder_path,
                    'normalized_path': str(folder_path_obj)
                }), 400
                
        except Exception as path_error:
            error_msg = f"경로 처리 중 오류 발생: {str(path_error)}"
            logger.error(f"{error_msg}\n원본 경로: {folder_path}", exc_info=True)
            return jsonify({
                'success': False, 
                'error': f'경로 처리 중 오류가 발생했습니다: {str(path_error)}',
                'original_path': folder_path
            }), 400
        
        logger.info(f"폴더 스캔 시작: {folder_path}")
        print(f"폴더 스캔을 시작합니다: {folder_path}")
        
        # 문서 스캔 (모든 문서 포함)
        try:
            all_docs = scan_directory_for_foreign_docs(folder_path_obj)
            logger.info(f"스캔 완료: {len(all_docs)}개의 문서를 찾았습니다.")
            print(f"스캔 완료: {len(all_docs)}개의 문서를 찾았습니다.")
            
            # 외국어 문서 수 계산
            foreign_count = sum(1 for doc in all_docs if doc.get('is_foreign', False))
            
            return jsonify({
                'success': True,
                'files': all_docs,
                'total_count': len(all_docs),
                'foreign_count': foreign_count,
                'message': f'총 {len(all_docs)}개 문서 중 {foreign_count}개의 외국어 문서가 있습니다.'
            })
            
        except Exception as scan_error:
            error_msg = f"문서 스캔 중 오류 발생: {str(scan_error)}"
            logger.error(error_msg, exc_info=True)
            print(error_msg)
            return jsonify({
                'success': False, 
                'error': f'문서 스캔 중 오류가 발생했습니다: {str(scan_error)}'
            }), 500
        
    except json.JSONDecodeError:
        error_msg = "잘못된 JSON 형식의 요청"
        logger.error(error_msg)
        print(error_msg)
        return jsonify({'success': False, 'error': '잘못된 JSON 형식의 요청입니다.'}), 400
        
    except Exception as e:
        error_msg = f"폴더 스캔 중 예상치 못한 오류 발생: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return jsonify({
            'success': False, 
            'error': f'폴더 스캔 중 오류가 발생했습니다: {str(e)}'
        }), 500


@app.route('/api/convert-pdf-to-markdown', methods=['POST'])
def convert_pdf_to_markdown():
    """
    PDF 파일을 마크다운으로 변환합니다.
    
    요청 본문:
        {
            "pdf_path": "PDF 파일 경로",
            "output_dir": "출력 디렉토리 (선택사항)",
            "use_ocr": true/false (선택사항, 기본값: false)
        }
        
    응답:
        성공 시:
            {
                "success": true,
                "markdown_path": "생성된 마크다운 파일 경로",
                "file_size_kb": 파일_크기_KB
            }
        실패 시:
            {
                "success": false,
                "error": "오류 메시지"
            }
    """
    try:
        data = request.get_json()
        pdf_path = data.get('pdf_path')
        output_dir = data.get('output_dir')
        use_ocr = data.get('use_ocr', False)
        
        # 필수 파라미터 검증
        if not pdf_path:
            return jsonify({
                'success': False,
                'error': 'PDF 파일 경로를 지정해주세요.'
            }), 400
            
        # PDF 파일 존재 여부 확인
        pdf_path = Path(pdf_path).resolve()
        if not pdf_path.exists() or not pdf_path.is_file():
            return jsonify({
                'success': False,
                'error': f'PDF 파일을 찾을 수 없습니다: {pdf_path}'
            }), 404
            
        # 출력 디렉토리 설정
        output_dir_path = Path(output_dir).resolve() if output_dir else None
        
        # 변환 실행
        try:
            markdown_path = file_utils.convert_pdf_to_markdown(
                pdf_path=pdf_path,
                output_dir=output_dir_path,
                use_ocr=use_ocr
            )
            
            # 파일 크기 확인 (KB 단위)
            file_size_kb = os.path.getsize(markdown_path) / 1024
            
            return jsonify({
                'success': True,
                'markdown_path': markdown_path,
                'file_size_kb': round(file_size_kb, 2)
            })
            
        except ImportError as e:
            logger.error(f"PDF 변환 모듈 로드 실패: {e}")
            return jsonify({
                'success': False,
                'error': 'PDF 변환을 위한 모듈이 설치되지 않았습니다. docling 패키지를 설치해주세요.'
            }), 500
            
        except Exception as e:
            logger.error(f"PDF 변환 중 오류 발생: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'PDF 변환 중 오류가 발생했습니다: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"API 처리 중 오류 발생: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'요청 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500


@app.route('/api/check-language', methods=['POST'])
def check_language():
    """
    파일의 언어를 감지하여 반환합니다.
    
    요청 본문:
        {
            "path": "파일 경로"
        }
        
    응답:
        성공 시:
            {
                "success": true,
                "language": "ko",
                "confidence": 95.5,
                "language_name": "Korean"
            }
        실패 시:
            {
                "success": false,
                "error": "오류 메시지"
            }
    """
    try:
        data = request.get_json()
        file_path = data.get('path')
        
        if not file_path or not os.path.isfile(file_path):
            return jsonify({
                'success': False,
                'error': '파일 경로가 유효하지 않습니다.'
            }), 400
        
        # 파일 크기 확인 (100MB 제한)
        file_size = os.path.getsize(file_path)
        if file_size > 100 * 1024 * 1024:
            return jsonify({
                'success': False,
                'error': '파일 크기가 너무 큽니다 (최대 100MB까지 지원)'
            }), 400
        
        # 언어 감지
        lang, confidence = file_utils.detect_document_language(Path(file_path))
        
        # 언어 코드를 언어명으로 변환
        language_names = {
            'ko': 'Korean',
            'en': 'English',
            'ja': 'Japanese',
            'zh-cn': 'Chinese (Simplified)',
            'zh-tw': 'Chinese (Traditional)',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'ru': 'Russian',
            'ar': 'Arabic',
            'pt': 'Portuguese',
            'it': 'Italian',
            'vi': 'Vietnamese',
            'th': 'Thai',
            'id': 'Indonesian',
            'hi': 'Hindi'
        }
        
        language_name = language_names.get(lang, f'Unknown ({lang})')
        
        return jsonify({
            'success': True,
            'language': lang,
            'confidence': round(confidence * 100, 1),
            'language_name': language_name
        })
        
    except Exception as e:
        logger.error(f"언어 감지 중 오류 발생: {e}")
        return jsonify({
            'success': False,
            'error': f'언어 감지 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/select-file', methods=['POST'])
def select_file():
    """
    파일을 선택하고 파일 정보를 반환합니다.
    
    요청 본문:
        {
            "path": "파일 경로"
        }
        
    응답:
        성공 시:
            {
                "success": true,
                "file": {
                    "name": "파일명",
                    "display_name": "표시용_파일명(언어포함)",
                    "path": "전체 경로",
                    "size": 파일_크기_바이트,
                    "type": "파일_확장자",
                    "last_modified": 수정_타임스탬프,
                    "language": "감지된_언어_코드",
                    "language_name": "언어_이름",
                    "confidence": 신뢰도_0_100,
                    "pages": 페이지_수(PDF_경우),
                    "is_translatable": 번역_가능_여부
                }
            }
        실패 시:
            {
                "success": false,
                "error": "오류 메시지"
            }
    """
    try:
        data = request.get_json()
        file_path = data.get('path')
        
        # 필수 파라미터 검증
        if not file_path:
            return jsonify({
                'success': False,
                'error': '파일 경로를 지정해주세요.'
            }), 400
            
        # 파일 존재 여부 확인
        if not os.path.isfile(file_path):
            return jsonify({
                'success': False,
                'error': f'파일을 찾을 수 없습니다: {file_path}'
            }), 404
            
        # 파일 경로 정규화
        file_path = os.path.abspath(file_path)
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # 기본 파일 정보
        file_info = {
            'name': file_name,
            'display_name': file_name,  # UI에 표시할 파일명 (언어 정보 포함)
            'path': file_path,
            'size': file_size,
            'type': file_ext[1:] if file_ext else 'unknown',
            'last_modified': int(os.path.getmtime(file_path)),
            'language': None,
            'language_name': None,
            'confidence': 0,
            'pages': 0,
            'is_translatable': file_ext in ['.txt', '.md', '.markdown', '.pdf']
        }
        
        # PDF 파일인 경우 추가 정보 수집
        if file_ext == '.pdf':
            try:
                if Pdf2ImageAvailable:
                    info = pdfinfo_from_path(file_path, userpw=None, poppler_path=None)
                    file_info['pages'] = info['Pages']
                else:
                    # PyPDF2로 대체
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        file_info['pages'] = len(reader.pages)
            except Exception as e:
                logger.warning(f"PDF 정보를 가져오는 중 오류 발생: {e}")
                file_info['pages'] = 0
        
        # 언어 감지 (텍스트, 마크다운, PDF)
        if file_ext in ['.txt', '.md', '.markdown', '.pdf']:
            try:
                # file_utils의 언어 감지 함수 사용
                lang, confidence = file_utils.detect_document_language(Path(file_path))
                
                # 언어 코드를 언어명으로 변환
                language_names = {
                    'ko': 'Korean',
                    'en': 'English',
                    'ja': 'Japanese',
                    'zh-cn': 'Chinese (Simplified)',
                    'zh-tw': 'Chinese (Traditional)',
                    'es': 'Spanish',
                    'fr': 'French',
                    'de': 'German',
                    'ru': 'Russian',
                    'pt': 'Portuguese',
                    'it': 'Italian',
                    'vi': 'Vietnamese',
                    'th': 'Thai',
                    'id': 'Indonesian',
                    'hi': 'Hindi'
                }
                
                file_info.update({
                    'language': lang,
                    'language_name': language_names.get(lang, f'Unknown ({lang})'),
                    'confidence': round(confidence * 100, 1)  # 백분율로 변환
                })
                
                # 파일명에 언어 정보 추가 (UI 표시용)
                if confidence > 0.5:  # 신뢰도가 50% 이상인 경우에만 언어 표시
                    name_without_ext = file_path.stem
                    ext = file_path.suffix
                    
                    # 기존에 언어 코드가 이미 붙어있는지 확인하고 제거
                    for code in language_names.keys():
                        if name_without_ext.lower().endswith(f'_{code.lower()}'):
                            name_without_ext = name_without_ext[:-len(f'_{code.upper()}')]
                            break
                    
                    # 새로운 언어 코드 추가
                    display_name = f"{name_without_ext} ({lang.upper()}){ext}"
                    file_info["display_name"] = display_name
                
            except Exception as e:
                logger.warning(f"언어 감지 중 오류 발생: {e}")
                file_info.update({
                    'language': 'unknown',
                    'language_name': 'Unknown',
                    'confidence': 0
                })
        
        return jsonify({
            'success': True,
            'file': file_info
        })
        
    except Exception as e:
        logger.error(f"파일 선택 중 오류 발생: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'파일 정보를 가져오는 중 오류가 발생했습니다: {str(e)}'
        }), 500
@app.route('/api/view-pdf', methods=['POST'])
def view_pdf():
    """
    PDF 파일의 특정 페이지를 이미지로 변환하여 반환합니다.
    
    Args:
        request (dict): 요청 본문
            - path (str): PDF 파일 경로 (필수)
            - page (int): 페이지 번호 (1부터 시작, 선택사항, 기본값: 1)
            - dpi (int): 이미지 해상도 (선택사항, 기본값: 200)
    
    Returns:
        dict: JSON 응답
        - 성공 시:
            {
                "success": true,
                "image": "base64_인코딩된_이미지_데이터",
                "total_pages": int,  # 전체 페이지 수
                "current_page": int,  # 현재 페이지 번호
                "dpi": int,           # 사용된 해상도
                "original_size": str,  # 원본 이미지 크기 (예: "800x1200")
                "display_size": str    # 표시 크기 (예: "1200x1800")
            }
        - 실패 시:
            {
                "success": false,
                "error": str  # 오류 메시지
            }
    """
    try:
        data = request.get_json()
        path = data.get('path')
        page = int(data.get('page', 1))
        dpi = int(data.get('dpi', 200))  # 기본 DPI를 200으로 설정
        
        # 필수 파라미터 검증
        if not path:
            return jsonify({
                'success': False,
                'error': 'PDF 파일 경로를 지정해주세요.'
            }), 400
            
        # 파일 존재 여부 확인
        if not os.path.isfile(path):
            return jsonify({
                'success': False,
                'error': f'PDF 파일을 찾을 수 없습니다: {path}'
            }), 404
        
        # PDF 정보 가져오기
        try:
            pdf_info = pdfinfo_from_path(path)
            total_pages = pdf_info.get('Pages', 1)
            
            # 페이지 번호 유효성 검사
            if page < 1 or page > total_pages:
                return jsonify({
                    'success': False,
                    'error': f'유효하지 않은 페이지 번호입니다. (1-{total_pages} 사이의 값을 사용하세요)'
                }), 400
                
            # PDF에서 이미지 변환 (고해상도로 변환)
            images = convert_from_path(
                path, 
                first_page=page, 
                last_page=page,
                dpi=dpi,
                thread_count=4,  # 멀티스레딩으로 성능 개선
                poppler_path=globals().get('POPPLER_PATH', None)
            )
            
            if not images:
                return jsonify({
                    'success': False,
                    'error': 'PDF에서 이미지를 추출할 수 없습니다.'
                }), 500
            
            # 원본 이미지 크기 저장
            width, height = images[0].size
            
            # 이미지 품질 향상을 위해 1.5배로 확대 (선택사항)
            new_size = (int(width * 1.5), int(height * 1.5))
            resized_image = images[0].resize(new_size, Image.Resampling.LANCZOS)
            
            # 이미지 선명도 향상
            enhancer = ImageEnhance.Sharpness(resized_image)
            enhanced_image = enhancer.enhance(1.5)  # 선명도 50% 증가
            
            # 이미지를 base64로 인코딩
            buffered = BytesIO()
            enhanced_image.save(buffered, format='PNG', quality=95, dpi=(dpi, dpi))
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # 메모리 정리
            del images
            
            return jsonify({
                'success': True,
                'image': img_str, 
                'total_pages': total_pages,
                'current_page': page,
                'dpi': dpi,
                'original_size': f"{width}x{height}",
                'display_size': f"{new_size[0]}x{new_size[1]}"
            })
            
        except Exception as e:
            logger.error(f"PDF 처리 중 오류 발생: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'PDF 처리 중 오류가 발생했습니다: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"PDF 뷰어 오류: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'PDF를 로드하는 중 오류가 발생했습니다: {str(e)}'
        }), 500


@app.route('/api/translate', methods=['POST'])
def translate():
    path = request.json['path']
    # 데몬 스레드로 설정하여 프로그램 종료 시 자동으로 종료되도록 함
    thread = threading.Thread(target=tasks.run_translation, args=(path,), daemon=True)
    thread.start()
    return jsonify({'status': 'started', 'path': path})


@app.route('/api/translation-status')
def translation_status():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': '경로가 지정되지 않았습니다.'}), 400
    
    include_partial = request.args.get('include_partial', 'false').lower() == 'true'
    
    print(f"[DEBUG] 번역 상태 요청 - 경로: {path}, 부분결과포함: {include_partial}")
    
    # 번역 상태 확인
    status_data = tasks.progress_manager.get(path)
    print(f"[DEBUG] progress_manager 상태 데이터: {status_data}")
    
    if status_data is None:
        print(f"[DEBUG] 상태 데이터 없음 - not_found 반환")
        return jsonify({'status': 'not_found'})
    
    # 상태가 딕셔너리인 경우 (새 형식)
    if isinstance(status_data, dict):
        response = {
            'status': status_data.get('status', 'unknown'),
        }
        
        print(f"[DEBUG] 현재 상태: {response['status']}")
        
        # 번역 진행 상황 정보 추가
        if status_data.get('status') == 'running':
            # 총 청크 수와 완료된 청크 수
            total_chunks = status_data.get('total_chunks', 0)
            chunks_completed = status_data.get('chunks_completed', 0)
            current_chunk = status_data.get('current_chunk', 0)
            
            # 진행률 계산 (0-100%)
            progress_percent = (chunks_completed / total_chunks * 100) if total_chunks > 0 else 0
            
            response.update({
                'total_chunks': total_chunks,
                'current_chunk': current_chunk,
                'chunks_completed': chunks_completed,
                'progress_percent': round(progress_percent, 1),
                'chunks_info': status_data.get('chunks_info', [])
            })
            
            print(f"[DEBUG] 진행률 정보 - 완료: {chunks_completed}/{total_chunks} ({progress_percent:.1f}%)")
            
            # 부분 결과 추가 (선택적)
            if include_partial:
                partial_results = tasks.progress_manager.get_partial_results(path)
                if partial_results:
                    response['partial_results'] = partial_results
                    print(f"[DEBUG] 부분 결과 포함 - 길이: {len(partial_results)}자")
        
        # 오류 정보 추가
        if status_data.get('status') == 'error' and 'error' in status_data:
            response['error'] = status_data['error']
            print(f"[DEBUG] 오류 상태: {response['error']}")
            
        print(f"[DEBUG] 최종 응답: {response}")
        return jsonify(response)
    
    # 이전 형식의 상태 처리 (하위 호환성)
    elif status_data == 'running':
        print(f"[DEBUG] 이전 형식 - running 상태")
        return jsonify({'status': 'running'})
    elif status_data == 'done':
        print(f"[DEBUG] 이전 형식 - done 상태")
        return jsonify({'status': 'completed'})
    else:
        print(f"[DEBUG] 이전 형식 - 기타 상태: {status_data}")
        return jsonify({'status': status_data})


@app.route('/api/translation-result')
def translation_result():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': '경로가 지정되지 않았습니다.'}), 400
    
    # Use the helper function from tasks.py to get the new path
    translated_path = get_translated_file_path(path)
    
    if not translated_path.exists():
        return jsonify({'error': f'번역 파일을 찾을 수 없습니다: {translated_path}'}), 404
    
    try:
        with open(translated_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': f'번역 파일을 읽는 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/read-file')
def read_file():
    import os
    from pathlib import Path
    
    file_path = request.args.get('path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except UnicodeDecodeError:
        try:
            # UTF-8 실패 시 다른 인코딩 시도
            with open(file_path, 'r', encoding='cp949') as f:
                content = f.read()
            return jsonify({'content': content})
        except Exception as e:
            return jsonify({'error': f'파일을 읽는 중 오류가 발생했습니다: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'파일을 읽는 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/download')
def download_file():
    import os
    from flask import send_file
    
    file_path = request.args.get('path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
    
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
    except Exception as e:
        return jsonify({'error': f'파일 다운로드 중 오류가 발생했습니다: {str(e)}'}), 500


# Ollama server process
ollama_process = None

def is_ollama_running():
    """Checks if the Ollama server is running and responsive."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        response.raise_for_status() # Raise an exception for HTTP errors
        logger.info("Ollama server is already running.")
        return True
    except requests.exceptions.ConnectionError:
        logger.info("Ollama server is not running (connection error).")
        return False
    except requests.exceptions.Timeout:
        logger.warning("Ollama server timed out. It might be starting up or unresponsive.")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking Ollama status: {e}")
        return False

def start_ollama_server():
    """Starts the Ollama server if it's not already running."""
    global ollama_process
    if is_ollama_running():
        return

    try:
        logger.info("Attempting to start Ollama server...")
        ollama_executable = "ollama" # Assumes 'ollama' is in PATH

        if os.name == 'nt': # For Windows
            from subprocess import CREATE_NO_WINDOW
            ollama_process = subprocess.Popen(
                [ollama_executable, "serve"],
                creationflags=CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else: # For macOS/Linux
            ollama_process = subprocess.Popen(
                [ollama_executable, "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

        logger.info(f"Ollama server process started with PID: {ollama_process.pid if ollama_process else 'Unknown'}.")
        time.sleep(5) # Adjust as needed, give server time to start
        if not is_ollama_running():
            logger.warning("Ollama server process was started, but it's not responsive yet.")
            if ollama_process:
                try:
                    stdout, stderr = ollama_process.communicate(timeout=1) # Non-blocking check for output
                    if stdout and stdout.strip():
                        logger.info(f"Ollama server stdout: {stdout.decode(errors='ignore').strip()}")
                    if stderr and stderr.strip():
                        logger.error(f"Ollama server stderr: {stderr.decode(errors='ignore').strip()}")
                except subprocess.TimeoutExpired:
                    logger.info("Ollama server process is still running, no immediate output.")
        else:
            logger.info("Ollama server is now running and responsive.")

    except FileNotFoundError:
        logger.error(
            f"'{ollama_executable}' command not found. Please ensure Ollama is installed and in your system's PATH."
        )
        ollama_process = None
    except Exception as e:
        logger.error(f"Failed to start Ollama server: {e}")
        ollama_process = None

def stop_ollama_server():
    """Stops the Ollama server if it was started by this application."""
    global ollama_process
    if ollama_process and ollama_process.poll() is None: # Check if process exists and is running
        logger.info(f"Stopping Ollama server (PID: {ollama_process.pid})...")
        try:
            ollama_process.terminate() # Send SIGTERM
            ollama_process.wait(timeout=10) # Wait for graceful shutdown
            logger.info("Ollama server terminated gracefully.")
        except subprocess.TimeoutExpired:
            logger.warning("Ollama server did not terminate gracefully within timeout. Forcing kill...")
            ollama_process.kill() # Send SIGKILL
            ollama_process.wait() # Wait for forced shutdown
            logger.info("Ollama server killed.")
        except Exception as e:
            logger.error(f"Error stopping Ollama server: {e}")
        finally:
            ollama_process = None
    elif ollama_process and ollama_process.poll() is not None:
        logger.info("Ollama server process was already terminated or not started by this app.")
        ollama_process = None
    else:
        logger.info("No Ollama server process to stop (was not started by this app or already stopped).")


if __name__ == '__main__':
    # Start Ollama server
    start_ollama_server()

    # Register stop_ollama_server to be called on exit
    atexit.register(stop_ollama_server)

    # 서버 종료 시 자원을 정리하도록 설정 (Original line)
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    # Run Flask app
    # use_reloader=False is important when managing external processes like Ollama,
    # as the reloader can cause multiple instances or issues with process management.
    logger.info("Starting Flask application server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)