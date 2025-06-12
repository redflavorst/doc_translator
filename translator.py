import re
import time
import os
import torch
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import yaml

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""NLLB 기반 문서 번역 시스템"""

PROMPT_FILE = Path('prompts/tax_translation_prompt.yaml')

# YAML 파일이 존재하는 경우에만 로드
PROMPTS = {}
if PROMPT_FILE.exists():
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            PROMPTS = yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"프롬프트 파일 로드 실패: {e}")

# 청크 크기 설정
MAX_CHUNK_SIZE = 1000
MIN_CHUNK_SIZE = 500
HEADER_PATTERN = re.compile(r'^(#{1,6}\s.+)', re.MULTILINE)

# NLLB 언어 코드 매핑
NLLB_LANGUAGE_CODES = {
    'en': 'eng_Latn',     # English
    'ja': 'jpn_Jpan',     # Japanese  
    'zh': 'zho_Hans',     # Chinese (Simplified)
    'zh-cn': 'zho_Hans',  # Chinese (Simplified)
    'zh-tw': 'zho_Hant',  # Chinese (Traditional)
    'ko': 'kor_Hang',     # Korean
    'es': 'spa_Latn',     # Spanish
    'fr': 'fra_Latn',     # French
    'de': 'deu_Latn',     # German
    'ru': 'rus_Cyrl',     # Russian
    'ar': 'arb_Arab',     # Arabic
    'pt': 'por_Latn',     # Portuguese
    'it': 'ita_Latn',     # Italian
    'vi': 'vie_Latn',     # Vietnamese
    'th': 'tha_Thai',     # Thai
    'id': 'ind_Latn',     # Indonesian
    'hi': 'hin_Deva',     # Hindi
    'tr': 'tur_Latn',     # Turkish
    'nl': 'nld_Latn',     # Dutch
    'pl': 'pol_Latn',     # Polish
    'sv': 'swe_Latn',     # Swedish
    'da': 'dan_Latn',     # Danish
    'no': 'nor_Latn',     # Norwegian
    'fi': 'fin_Latn',     # Finnish
}

class NLLBTranslator:
    """NLLB 기반 번역기 클래스"""
    
    def __init__(self, model_path: str = None, device: str = "auto"):
        """
        NLLB 번역기 초기화
        
        Args:
            model_path: 로컬 모델 경로 또는 HuggingFace 모델명
            device: 사용할 디바이스 ("auto", "cpu", "cuda")
        """
        # 로컬 모델 경로 자동 감지
        if model_path is None:
            model_path = self._find_local_model()
        
        self.model_name = model_path
        self.device = self._get_device(device)
        self.tokenizer = None
        self.model = None
        self.translator = None
        self._initialized = False
        
        logger.info(f"NLLB 번역기 초기화 중... (모델: {model_path}, 디바이스: {self.device})")
        
    def _find_local_model(self) -> str:
        """로컬에 설치된 NLLB 모델을 찾아서 경로 반환"""
        possible_paths = [
            # 현재 경로 기준 상대 경로들
            "../nllb_1.3b_int8",
            "../../nllb_1.3b_int8", 
            "../../../nllb_1.3b_int8",
            "../../../../nllb_1.3b_int8",
            # 절대 경로들 (사용자별 일반적 위치)
            os.path.expanduser("~/nllb_1.3b_int8"),
            os.path.expanduser("~/models/nllb_1.3b_int8"),
            # 프로젝트 내 models 폴더
            "./models/nllb_1.3b_int8",
            "./nllb_1.3b_int8",
            # 현재 작업 디렉토리 기준
            "nllb_1.3b_int8",
        ]
        
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                # 필수 파일들이 있는지 확인
                required_files = ['config.json', 'tokenizer.json']
                if all(os.path.exists(os.path.join(abs_path, f)) for f in required_files):
                    logger.info(f"로컬 NLLB 모델 발견: {abs_path}")
                    return abs_path
        
        # 로컬 모델이 없으면 기본 HuggingFace 모델 사용
        logger.info("로컬 NLLB 모델을 찾을 수 없어 기본 모델을 사용합니다.")
        return "facebook/nllb-200-distilled-600M"
        
    def _get_device(self, device_preference: str) -> str:
        """사용할 디바이스 결정"""
        if device_preference == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"  # Apple Silicon
            else:
                return "cpu"
        return device_preference
    
    def _initialize_model(self):
        """모델 초기화 (지연 로딩)"""
        if self._initialized:
            return
            
        try:
            logger.info("NLLB 모델 로딩 중...")
            
            # 로컬 모델인지 확인
            is_local_model = os.path.exists(self.model_name) and os.path.isdir(self.model_name)
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir="./models" if not is_local_model else None,
                local_files_only=is_local_model
            )
            
            # 모델 로드 (양자화 완전 비활성화)
            model_kwargs = {
                "cache_dir": "./models" if not is_local_model else None,
                "local_files_only": is_local_model,
                "torch_dtype": torch.float32,  # CPU에서는 float32 사용
                "low_cpu_mem_usage": True
            }
            
            logger.info("일반 Float32 모드로 모델 로딩 (양자화 비활성화)")
            
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                **model_kwargs
            ).to(self.device)
            
            # 파이프라인 생성
            self.translator = pipeline(
                "translation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float32  # CPU에서는 float32
            )
            
            self._initialized = True
            logger.info(f"NLLB 모델 로딩 완료 (디바이스: {self.device})")
            
        except Exception as e:
            logger.error(f"NLLB 모델 로딩 실패: {e}")
            raise RuntimeError(f"NLLB 모델 로딩 실패: {e}")
    
    def detect_language(self, text: str) -> str:
        """
        텍스트의 언어를 감지 (간단한 휴리스틱 사용)
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            str: 감지된 언어 코드
        """
        # 문자 기반 언어 감지
        text_sample = text[:1000]  # 처음 1000자만 사용
        
        # 한글 체크
        hangul_count = len(re.findall(r'[\uAC00-\uD7AF]', text_sample))
        if hangul_count > len(text_sample) * 0.1:
            return 'ko'
            
        # 일본어 체크 (히라가나, 가타카나)
        hiragana_count = len(re.findall(r'[\u3040-\u309F]', text_sample))
        katakana_count = len(re.findall(r'[\u30A0-\u30FF]', text_sample))
        if hiragana_count > 5 or katakana_count > 5:
            return 'ja'
            
        # 중국어 체크 (한자)
        chinese_count = len(re.findall(r'[\u4E00-\u9FAF]', text_sample))
        if chinese_count > len(text_sample) * 0.1:
            return 'zh'
            
        # 영어가 기본값
        return 'en'
    
    def translate_text(self, text: str, source_lang: str = "auto", target_lang: str = "ko") -> str:
        """
        텍스트 번역
        
        Args:
            text: 번역할 텍스트
            source_lang: 원본 언어 코드
            target_lang: 번역 대상 언어 코드
            
        Returns:
            str: 번역된 텍스트
        """
        if not text.strip():
            return text
            
        # 모델 초기화
        self._initialize_model()
        
        # 언어 자동 감지
        if source_lang == "auto":
            source_lang = self.detect_language(text)
            
        # NLLB 언어 코드로 변환
        src_code = NLLB_LANGUAGE_CODES.get(source_lang, 'eng_Latn')
        tgt_code = NLLB_LANGUAGE_CODES.get(target_lang, 'kor_Hang')
        
        # 이미 대상 언어인 경우 번역하지 않음
        if source_lang == target_lang:
            logger.info(f"텍스트가 이미 대상 언어({target_lang})입니다. 번역을 건너뜁니다.")
            return text
            
        try:
            logger.debug(f"번역 중: {source_lang} -> {target_lang} (길이: {len(text)})")
            
            # 텍스트가 너무 긴 경우 분할
            if len(text) > 512:
                return self._translate_long_text(text, src_code, tgt_code)
            
            # NLLB 번역 실행
            result = self.translator(
                text,
                src_lang=src_code,
                tgt_lang=tgt_code,
                max_length=1024
            )
            
            translated_text = result[0]['translation_text'] if isinstance(result, list) else result['translation_text']
            return translated_text.strip()
            
        except Exception as e:
            logger.error(f"번역 오류: {e}")
            return f"[번역 오류: {str(e)}]"
    
    def _translate_long_text(self, text: str, src_code: str, tgt_code: str) -> str:
        """긴 텍스트를 분할하여 번역"""
        sentences = self._split_into_sentences(text)
        translated_sentences = []
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk + sentence) > 512:
                if current_chunk:
                    # 현재 청크 번역
                    result = self.translator(
                        current_chunk.strip(),
                        src_lang=src_code,
                        tgt_lang=tgt_code,
                        max_length=1024
                    )
                    chunk_translation = result[0]['translation_text'] if isinstance(result, list) else result['translation_text']
                    translated_sentences.append(chunk_translation.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        # 마지막 청크 처리
        if current_chunk.strip():
            result = self.translator(
                current_chunk.strip(),
                src_lang=src_code,
                tgt_lang=tgt_code,
                max_length=1024
            )
            chunk_translation = result[0]['translation_text'] if isinstance(result, list) else result['translation_text']
            translated_sentences.append(chunk_translation.strip())
        
        return ' '.join(translated_sentences)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분할"""
        # 간단한 문장 분할 (개선 가능)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s + ' ' for s in sentences if s.strip()]

# 전역 번역기 인스턴스
_translator_instance: Optional[NLLBTranslator] = None

def get_translator() -> NLLBTranslator:
    """전역 번역기 인스턴스 반환"""
    global _translator_instance
    if _translator_instance is None:
        # 다운로드한 모델 경로 사용
        model_path = "./models/nllb-200-distilled-600M"
        _translator_instance = NLLBTranslator(model_path=model_path, device="cpu")
    return _translator_instance

def split_text_by_size(text: str, max_size: int) -> List[str]:
    """텍스트를 최대 크기에 맞게 분할"""
    if len(text) <= max_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_size
        if end >= len(text):
            chunks.append(text[start:])
            break

        # 가능하면 문단이나 문장 경계에서 자름
        paragraph_end = text.rfind('\n\n', start, end)
        if paragraph_end != -1 and paragraph_end > start:
            end = paragraph_end + 2
        else:
            sentence_end = max([
                text.rfind('. ', start, end),
                text.rfind('! ', start, end),
                text.rfind('? ', start, end),
                text.rfind('。', start, end),  # 일본어 마침표
                text.rfind('！', start, end),  # 일본어 느낌표
                text.rfind('？', start, end),  # 일본어 물음표
            ])
            if sentence_end != -1 and sentence_end > start:
                end = sentence_end + 1
        
        chunks.append(text[start:end])
        start = end
    return chunks

def split_markdown_by_headers(markdown_text: str) -> List[Dict[str, Any]]:
    """마크다운 텍스트를 헤더 단위로 분할하고 메타데이터 반환"""
    header_matches = list(HEADER_PATTERN.finditer(markdown_text))
    
    if not header_matches:
        # 헤더가 없으면 길이 기준으로 분할
        text_chunks = split_text_by_size(markdown_text, MAX_CHUNK_SIZE)
        return [
            {
                'text': chunk,
                'header': f"섹션 {i+1}",
                'level': 0,
                'size': len(chunk)
            }
            for i, chunk in enumerate(text_chunks)
        ]

    # 각 헤더 구간의 정보를 저장
    sections = []
    for i, match in enumerate(header_matches):
        current_start = match.start()
        current_header = match.group(0).strip()
        current_level = len(current_header) - len(current_header.lstrip('#'))
        next_start = header_matches[i+1].start() if i < len(header_matches) - 1 else len(markdown_text)
        section_text = markdown_text[current_start:next_start].strip()
        
        sections.append({
            'text': section_text,
            'header': current_header,
            'level': current_level,
            'size': len(section_text),
            'start': current_start,
            'end': next_start,
        })

    # 너무 작은 섹션은 앞부분과 합침
    merged_sections = []
    current = None
    
    for section in sections:
        if current is None:
            current = section.copy()
        elif section['size'] < MIN_CHUNK_SIZE and current['size'] + section['size'] <= MAX_CHUNK_SIZE:
            current['text'] += '\n\n' + section['text']
            current['size'] += section['size']
            current['end'] = section['end']
            # 헤더는 첫 번째 섹션의 것을 유지
        else:
            merged_sections.append(current)
            current = section.copy()
    
    if current is not None:
        merged_sections.append(current)

    # 너무 큰 섹션은 다시 분할
    final_chunks = []
    for section in merged_sections:
        if section['size'] > MAX_CHUNK_SIZE:
            sub_chunks = split_text_by_size(section['text'], MAX_CHUNK_SIZE)
            for j, sub_chunk in enumerate(sub_chunks):
                final_chunks.append({
                    'text': sub_chunk,
                    'header': f"{section['header']} (part {j+1})",
                    'level': section['level'],
                    'size': len(sub_chunk)
                })
        else:
            final_chunks.append(section)
    
    return final_chunks

def translate_chunk(text: str, idx: Optional[int] = None, total: Optional[int] = None, source_lang: str = "auto") -> str:
    """단일 청크를 NLLB로 번역"""
    if not text.strip():
        return text
        
    translator = get_translator()
    
    if idx is not None and total is not None:
        logger.info(f"청크 번역 중 {idx}/{total} (길이: {len(text)}자)")
    
    try:
        translated = translator.translate_text(text, source_lang=source_lang, target_lang="ko")
        return translated
        
    except Exception as e:
        error_msg = f"[번역 오류] {str(e)}"
        logger.error(f"청크 번역 실패 ({idx}/{total}): {e}")
        return error_msg

def translate_markdown(markdown_text: str, path: Optional[str] = None, source_lang: str = "auto") -> str:
    """마크다운 문서를 NLLB로 번역"""
    start_time = time.time()
    
    # 빈 텍스트 체크
    if not markdown_text or not markdown_text.strip():
        logger.warning("번역할 내용이 없습니다.")
        return markdown_text
    
    # 청크 분할
    chunks_info = split_markdown_by_headers(markdown_text)
    logger.info(f"총 {len(chunks_info)}개 청크로 분할됨")

    # 진행 상황 관리
    if path:
        try:
            from progress_manager import progress_manager
            progress_chunks = [
                {
                    'index': i,
                    'header': chunk['header'],
                    'size': chunk['size'],
                    'status': 'pending'
                } for i, chunk in enumerate(chunks_info)
            ]
            progress_manager.set_total_chunks(path, len(chunks_info), progress_chunks)
        except ImportError:
            logger.warning("progress_manager를 찾을 수 없습니다. 진행 상황이 표시되지 않습니다.")

    # 번역 실행
    translated_chunks = []
    for i, chunk_info in enumerate(chunks_info):
        chunk_text = chunk_info['text']
        
        if path:
            try:
                progress_manager.update_chunk_progress(path, i, 'processing')
            except NameError:
                pass  # progress_manager가 없는 경우 무시
        
        translated = translate_chunk(chunk_text, i + 1, len(chunks_info), source_lang)
        translated_chunks.append(translated)
        
        if path:
            try:
                progress_manager.add_chunk_result(path, i, translated)
            except NameError:
                pass

    # 최종 결과 조합
    end_time = time.time()
    elapsed_time = end_time - start_time
    formatted_time = f"{elapsed_time:.2f}초"

    final_translation = '\n\n'.join(translated_chunks)
    final_translation += f"\n\n---\n**번역 정보**\n- 번역 엔진: NLLB-200\n- 소요 시간: {formatted_time}\n- 청크 수: {len(chunks_info)}개\n---"
    
    logger.info(f"번역 완료: {len(chunks_info)}개 청크, 소요 시간: {formatted_time}")
    return final_translation

def translate_paragraph(text: str, source_lang: str = "auto") -> str:
    """이전 버전 호환을 위한 단순 래퍼"""
    logger.warning("translate_paragraph()는 deprecated입니다. translate_markdown() 사용을 권장합니다.")
    return translate_chunk(text, source_lang=source_lang)

# 모듈 종료 시 정리
def cleanup():
    """리소스 정리"""
    global _translator_instance
    if _translator_instance is not None:
        # GPU 메모리 정리
        if hasattr(_translator_instance, 'model') and _translator_instance.model is not None:
            del _translator_instance.model
        if hasattr(_translator_instance, 'tokenizer') and _translator_instance.tokenizer is not None:
            del _translator_instance.tokenizer
        if hasattr(_translator_instance, 'translator') and _translator_instance.translator is not None:
            del _translator_instance.translator
        _translator_instance = None
        
        # PyTorch 캐시 정리
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("NLLB 번역기 리소스 정리 완료")

# 모듈 종료 시 자동 정리
import atexit
atexit.register(cleanup)