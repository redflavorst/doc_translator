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
            # 프로젝트 내 models 폴더 (실제 구조에 맞게 수정)
            "./models/nllb-200-distilled-600M",
            "./models/models--facebook--nllb-200-distilled-600M/snapshots/f8d333a098d19b4fd9a8b18f94170487ad3f821d",
            # 기존 경로들
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
            logger.debug(f"모델 경로 확인 중: {abs_path}")
            if os.path.exists(abs_path):
                # 필수 파일들이 있는지 확인
                required_files = ['config.json', 'tokenizer.json']
                missing_files = []
                for f in required_files:
                    file_path = os.path.join(abs_path, f)
                    if not os.path.exists(file_path):
                        missing_files.append(f)
                
                if not missing_files:
                    logger.info(f"로컬 NLLB 모델 발견: {abs_path}")
                    return abs_path
                else:
                    logger.debug(f"경로 {abs_path}에서 누락된 파일들: {missing_files}")
            else:
                logger.debug(f"경로가 존재하지 않음: {abs_path}")
        
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
                "low_cpu_mem_usage": True
            }
            
            # torch_dtype 설정 (버전 호환성 확인)
            try:
                model_kwargs["torch_dtype"] = torch.float32
            except AttributeError:
                logger.warning("torch.float32를 찾을 수 없어 기본 dtype을 사용합니다.")
            
            logger.info("일반 Float32 모드로 모델 로딩 (양자화 비활성화)")
            
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                **model_kwargs
            ).to(self.device)
            
            # 파이프라인 생성
            pipeline_kwargs = {
                "task": "translation",
                "model": self.model,
                "tokenizer": self.tokenizer,
                "device": 0 if self.device == "cuda" else -1
            }
            
            # torch_dtype 설정 (버전 호환성 확인)
            try:
                pipeline_kwargs["torch_dtype"] = torch.float32
            except AttributeError:
                logger.warning("파이프라인에서 torch_dtype을 설정할 수 없습니다.")
            
            self.translator = pipeline(**pipeline_kwargs)
            
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
            
            # 텍스트 전처리 (반복 패턴 제거)
            preprocessed_text = self._preprocess_text(text)
            
            # 텍스트가 너무 긴 경우 분할
            if len(preprocessed_text) > 400:  # 더 작은 청크로 분할
                return self._translate_long_text(preprocessed_text, src_code, tgt_code)
            
            # NLLB 번역 실행 (더욱 보수적인 파라미터)
            result = self.translator(
                preprocessed_text,
                src_lang=src_code,
                tgt_lang=tgt_code,
                max_length=min(len(preprocessed_text) * 2, 500),  # 입력 길이의 2배 또는 500자 중 작은 값
                min_length=max(1, len(preprocessed_text) // 4),    # 최소 길이 설정
                num_beams=2,     # 빔 수 줄임 (안정성 향상)
                do_sample=False, # 샘플링 비활성화
                repetition_penalty=1.5,  # 반복 억제 강화
                no_repeat_ngram_size=4,  # 4-gram 반복 방지
                length_penalty=0.8,      # 길이 패널티 (짧은 번역 선호)
                early_stopping=True      # 조기 종료
            )
            
            translated_text = result[0]['translation_text'] if isinstance(result, list) else result['translation_text']
            
            # 후처리 (반복 패턴 제거)
            cleaned_text = self._postprocess_text(translated_text.strip())
            return cleaned_text
            
        except Exception as e:
            logger.error(f"번역 오류: {e}")
            return f"[번역 오류: {str(e)}]"
    
    def _translate_long_text(self, text: str, src_code: str, tgt_code: str) -> str:
        """긴 텍스트를 분할하여 번역"""
        sentences = self._split_into_sentences(text)
        translated_sentences = []
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk + sentence) > 400:  # 더 작은 청크 크기
                if current_chunk:
                    # 현재 청크 번역 (보수적 파라미터)
                    chunk_text = current_chunk.strip()
                    result = self.translator(
                        chunk_text,
                        src_lang=src_code,
                        tgt_lang=tgt_code,
                        max_length=min(len(chunk_text) * 2, 500),
                        min_length=max(1, len(chunk_text) // 4),
                        num_beams=2,
                        do_sample=False,
                        repetition_penalty=1.5,
                        no_repeat_ngram_size=4,
                        length_penalty=0.8,
                        early_stopping=True
                    )
                    chunk_translation = result[0]['translation_text'] if isinstance(result, list) else result['translation_text']
                    # 후처리 적용
                    cleaned_translation = self._postprocess_text(chunk_translation.strip())
                    translated_sentences.append(cleaned_translation)
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        # 마지막 청크 처리
        if current_chunk.strip():
            chunk_text = current_chunk.strip()
            result = self.translator(
                chunk_text,
                src_lang=src_code,
                tgt_lang=tgt_code,
                max_length=min(len(chunk_text) * 2, 500),
                min_length=max(1, len(chunk_text) // 4),
                num_beams=2,
                do_sample=False,
                repetition_penalty=1.5,
                no_repeat_ngram_size=4,
                length_penalty=0.8,
                early_stopping=True
            )
            chunk_translation = result[0]['translation_text'] if isinstance(result, list) else result['translation_text']
            # 후처리 적용
            cleaned_translation = self._postprocess_text(chunk_translation.strip())
            translated_sentences.append(cleaned_translation)
        
        return ' '.join(translated_sentences)
    
    def _preprocess_text(self, text: str) -> str:
        """번역 전 텍스트 전처리"""
        processed_text = text.strip()
        
        # 같은 단어가 연속으로 3번 이상 반복되는 경우 제거
        pattern = r'\b(\w+)(\s+\1){2,}\b'
        processed_text = re.sub(pattern, r'\1', processed_text, flags=re.IGNORECASE)
        
        # 같은 구문이 반복되는 경우 제거 (쉼표로 구분된)
        pattern = r'([^,]+),\s*\1(?:,\s*\1)*'
        processed_text = re.sub(pattern, r'\1', processed_text)
        
        # 극단적 반복 패턴 감지 및 제거
        words = processed_text.split()
        if len(words) > 10:
            word_count = {}
            for word in words:
                if len(word) > 2:  # 2글자 이상만 체크
                    word_count[word] = word_count.get(word, 0) + 1
            
            total_words = len([w for w in words if len(w) > 2])
            if total_words > 0:
                # 전체 단어의 30% 이상을 차지하는 단어가 있으면 문제가 있는 텍스트
                for word, count in word_count.items():
                    if count > max(3, total_words * 0.3):
                        logger.warning(f"반복 단어 감지 '{word}': {count}/{total_words}회 - 텍스트 단축")
                        # 첫 번째 문장만 사용
                        sentences = re.split(r'[.!?]+', text.strip())
                        first_sentence = sentences[0].strip() if sentences else text[:100]
                        return first_sentence + '.' if first_sentence and not first_sentence.endswith('.') else first_sentence
        
        # 텍스트가 너무 길면 분할 (400자 제한)
        if len(processed_text) > 400:
            sentences = re.split(r'(?<=[.!?])\s+', processed_text)
            result_text = ""
            for sentence in sentences:
                if len(result_text + sentence) <= 400:
                    result_text += sentence + " "
                else:
                    break
            processed_text = result_text.strip()
        
        return processed_text
    
    def _postprocess_text(self, text: str) -> str:
        """번역 후 텍스트 후처리"""
        if not text or not text.strip():
            return text
            
        processed_text = text.strip()
        
        # 극단적 반복 패턴 강력 제거
        # 1. 같은 단어가 3번 이상 연속 반복
        pattern = r'\b(\w+)(\s+\1){2,}\b'
        processed_text = re.sub(pattern, r'\1', processed_text, flags=re.IGNORECASE)
        
        # 2. 쉼표로 구분된 반복 패턴
        pattern = r'([^,]+),\s*\1(?:,\s*\1)+'
        processed_text = re.sub(pattern, r'\1', processed_text)
        
        # 3. 특정 단어/구가 과도하게 반복되는 경우 감지
        words = processed_text.split()
        if len(words) > 20:
            word_count = {}
            for word in words:
                if len(word) > 2 and word.isalpha():  # 알파벳 단어만
                    word_count[word] = word_count.get(word, 0) + 1
            
            # 단어 빈도가 비정상적으로 높은 경우
            total_meaningful_words = len([w for w in words if len(w) > 2 and w.isalpha()])
            if total_meaningful_words > 0:
                for word, count in word_count.items():
                    # 특정 단어가 20% 이상 또는 10회 이상 반복되면 문제
                    if count >= 10 or (count / total_meaningful_words) >= 0.2:
                        logger.error(f"번역 결과에서 과도한 반복 감지: '{word}' {count}회")
                        # 첫 번째 완전한 문장만 반환
                        sentences = re.split(r'[.!?]+', processed_text)
                        if sentences and len(sentences[0].strip()) > 10:
                            return sentences[0].strip() + '.'
                        else:
                            return "[번역 오류: 반복 패턴 감지됨]"
        
        # 4. 문장 중복 제거
        sentences = re.split(r'(?<=[.!?])\s+', processed_text)
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 5:  # 너무 짧은 문장 제외
                # 문장의 핵심 부분만 비교 (처음 50자)
                sentence_key = sentence[:50].lower()
                if sentence_key not in seen:
                    unique_sentences.append(sentence)
                    seen.add(sentence_key)
        
        result = ' '.join(unique_sentences)
        
        # 5. 최종 길이 제한 (너무 긴 번역 방지)
        if len(result) > 2000:
            sentences = re.split(r'(?<=[.!?])\s+', result)
            final_result = ""
            for sentence in sentences:
                if len(final_result + sentence) <= 2000:
                    final_result += sentence + " "
                else:
                    break
            result = final_result.strip()
        
        return result if result else "[번역 실패]"
    
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
        try:
            # 로컬 모델 자동 감지 사용
            _translator_instance = NLLBTranslator(model_path=None, device="cpu")
            # 초기화 강제 실행
            _translator_instance._initialize_model()
            logger.info("NLLB 번역기 초기화 완료")
        except Exception as e:
            logger.error(f"NLLB 번역기 초기화 실패: {e}")
            raise RuntimeError(f"번역기 초기화 실패: {e}")
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

def translate_markdown(markdown_text: str, path: Optional[str] = None, source_lang: str = "auto", use_sentence_mode: bool = False) -> str:
    """마크다운 문서를 NLLB로 번역 (적응형 하이브리드 방식)"""
    start_time = time.time()
    
    # 빈 텍스트 체크
    if not markdown_text or not markdown_text.strip():
        logger.warning("번역할 내용이 없습니다.")
        return markdown_text
    
    # 적응형 번역 모드 결정
    if use_sentence_mode:
        logger.info("강제 문장별 번역 모드 사용")
        return translate_markdown_by_sentences(markdown_text, path, source_lang, start_time)
    else:
        # 문서 특성 분석하여 최적 번역 방식 결정
        translation_mode = analyze_document_for_translation_mode(markdown_text)
        logger.info(f"적응형 번역 모드: {translation_mode}")
        
        if translation_mode == "hybrid":
            return translate_markdown_hybrid(markdown_text, path, source_lang, start_time)
        elif translation_mode == "sentence":
            return translate_markdown_by_sentences(markdown_text, path, source_lang, start_time)
    
    # 기본 청크 번역
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

def translate_markdown_by_sentences(markdown_text: str, path: Optional[str] = None, source_lang: str = "auto", start_time: float = None) -> str:
    """마크다운 문서를 문장별로 번역 (고품질 모드)"""
    if start_time is None:
        start_time = time.time()
    
    # 마크다운 구조 보존을 위한 파싱
    lines = markdown_text.split('\n')
    translated_lines = []
    total_sentences = 0
    translated_sentences = 0
    
    # 전체 문장 수 계산
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('```') and not line.startswith('|'):
            sentences = split_text_into_sentences(line)
            total_sentences += len([s for s in sentences if s.strip()])
    
    logger.info(f"총 {total_sentences}개 문장을 번역합니다")
    
    # 진행 상황 관리
    if path:
        try:
            from progress_manager import progress_manager
            progress_chunks = [
                {
                    'index': i,
                    'header': f"문장 {i+1}",
                    'size': 1,
                    'status': 'pending'
                } for i in range(total_sentences)
            ]
            progress_manager.set_total_chunks(path, total_sentences, progress_chunks)
        except ImportError:
            logger.warning("progress_manager를 찾을 수 없습니다.")
    
    # 각 라인별 처리
    for line in lines:
        line = line.strip()
        
        # 빈 줄
        if not line:
            translated_lines.append('')
            continue
            
        # 마크다운 헤더
        if line.startswith('#'):
            translated_lines.append(line)  # 헤더는 번역하지 않음
            continue
            
        # 코드 블록
        if line.startswith('```') or line.startswith('|'):
            translated_lines.append(line)  # 코드나 테이블은 번역하지 않음
            continue
            
        # 일반 텍스트 - 문장별 번역
        sentences = split_text_into_sentences(line)
        translated_line_parts = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if path:
                try:
                    progress_manager.update_chunk_progress(path, translated_sentences, 'processing')
                except NameError:
                    pass
            
            # 문장별 번역
            translated_sentence = translate_single_sentence(sentence, source_lang)
            translated_line_parts.append(translated_sentence)
            translated_sentences += 1
            
            if path:
                try:
                    progress_manager.add_chunk_result(path, translated_sentences - 1, translated_sentence)
                except NameError:
                    pass
            
            # 진행률 로그
            if translated_sentences % 10 == 0:
                logger.info(f"문장 번역 진행: {translated_sentences}/{total_sentences}")
        
        # 번역된 문장들을 하나의 라인으로 결합
        if translated_line_parts:
            translated_lines.append(' '.join(translated_line_parts))
        else:
            translated_lines.append('')
    
    # 최종 결과 조합
    end_time = time.time()
    elapsed_time = end_time - start_time
    formatted_time = f"{elapsed_time:.2f}초"
    
    final_translation = '\n'.join(translated_lines)
    final_translation += f"\n\n---\n**번역 정보**\n- 번역 엔진: NLLB-200 (문장별 모드)\n- 소요 시간: {formatted_time}\n- 번역된 문장 수: {translated_sentences}개\n---"
    
    logger.info(f"문장별 번역 완료: {translated_sentences}개 문장, 소요 시간: {formatted_time}")
    return final_translation

def split_text_into_sentences(text: str) -> List[str]:
    """텍스트를 문장으로 분할"""
    # 마침표, 느낌표, 물음표로 문장 분할
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]

def translate_single_sentence(sentence: str, source_lang: str = "auto") -> str:
    """단일 문장 번역 (최적화된 파라미터)"""
    if not sentence.strip():
        return sentence
        
    translator = get_translator()
    
    try:
        # 언어 자동 감지
        if source_lang == "auto":
            source_lang = translator.detect_language(sentence)
            
        # NLLB 언어 코드로 변환
        src_code = NLLB_LANGUAGE_CODES.get(source_lang, 'eng_Latn')
        tgt_code = NLLB_LANGUAGE_CODES.get('ko', 'kor_Hang')
        
        # 이미 한국어인 경우 번역하지 않음
        if source_lang == 'ko':
            return sentence
        
        # 모델 초기화 확인
        if not translator._initialized or translator.translator is None:
            logger.error("NLLB 모델이 초기화되지 않았습니다.")
            return sentence
        
        # 문장별 최적화된 번역 파라미터
        result = translator.translator(
            sentence,
            src_lang=src_code,
            tgt_lang=tgt_code,
            max_length=min(len(sentence) * 3, 200),  # 문장이므로 더 짧게
            min_length=max(1, len(sentence) // 3),
            num_beams=3,
            do_sample=False,
            repetition_penalty=1.3,
            no_repeat_ngram_size=3,
            length_penalty=1.0,
            early_stopping=True
        )
        
        translated_text = result[0]['translation_text'] if isinstance(result, list) else result['translation_text']
        
        # 간단한 후처리 (문장 단위이므로 가벼움)
        cleaned_text = translated_text.strip()
        
        # 극단적 반복만 체크
        words = cleaned_text.split()
        if len(words) > 5:
            word_count = {}
            for word in words:
                if len(word) > 2:
                    word_count[word] = word_count.get(word, 0) + 1
            
            for word, count in word_count.items():
                if count >= 3:  # 문장 내에서 3번 이상 반복
                    logger.warning(f"문장 내 반복 감지: '{word}' {count}회 - 원본 반환")
                    return sentence  # 문제가 있으면 원본 반환
        
        return cleaned_text
        
    except Exception as e:
        logger.error(f"문장 번역 실패: {e}")
        return sentence  # 오류 시 원본 반환

def analyze_document_for_translation_mode(markdown_text: str) -> str:
    """문서 특성을 분석하여 최적 번역 모드 결정"""
    lines = markdown_text.split('\n')
    total_lines = len([line for line in lines if line.strip()])
    
    # 문서 특성 분석
    long_sentences = 0
    bullet_points = 0
    legal_terms = 0
    headers = 0
    
    legal_keywords = ['agreement', 'consultant', 'commission', 'shall', 'liability', 'insurance', 'pursuant', 'herein', 'thereof']
    
    for line in lines:
        line = line.strip().lower()
        if not line:
            continue
            
        # 헤더 카운트
        if line.startswith('#'):
            headers += 1
            continue
            
        # 불릿 포인트
        if line.startswith('- ') or line.startswith('* '):
            bullet_points += 1
            
        # 긴 문장 (150자 이상)
        if len(line) > 150:
            long_sentences += 1
            
        # 법적 용어
        for keyword in legal_keywords:
            if keyword in line:
                legal_terms += 1
                break
    
    # 분석 결과
    logger.info(f"문서 분석: 총 {total_lines}줄, 긴 문장 {long_sentences}개, 법적 용어 {legal_terms}줄, 불릿 포인트 {bullet_points}개, 헤더 {headers}개")
    
    # 번역 모드 결정 로직
    if total_lines > 200:  # 매우 긴 문서
        if legal_terms / total_lines > 0.3:  # 법적 문서
            return "hybrid"  # 하이브리드 방식
        else:
            return "chunk"   # 청크 방식 (빠름)
    elif long_sentences > total_lines * 0.4:  # 긴 문장이 많음
        return "hybrid"      # 하이브리드 방식
    elif total_lines < 50:  # 짧은 문서
        return "sentence"    # 문장별 번역 (고품질)
    else:
        return "hybrid"      # 기본적으로 하이브리드

def translate_markdown_hybrid(markdown_text: str, path: Optional[str] = None, source_lang: str = "auto", start_time: float = None) -> str:
    """하이브리드 번역: 문장 길이에 따라 적응적으로 번역"""
    if start_time is None:
        start_time = time.time()
    
    # 헤더 기반 섹션 분할
    chunks_info = split_markdown_by_headers(markdown_text)
    logger.info(f"하이브리드 모드: {len(chunks_info)}개 섹션으로 분할")
    
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
            logger.warning("progress_manager를 찾을 수 없습니다.")
    
    translated_chunks = []
    
    for i, chunk_info in enumerate(chunks_info):
        chunk_text = chunk_info['text']
        chunk_size = chunk_info['size']
        
        if path:
            try:
                progress_manager.update_chunk_progress(path, i, 'processing')
            except NameError:
                pass
        
        # 청크 크기에 따른 적응적 번역
        if chunk_size < 200:  # 작은 청크 - 문장별 번역
            logger.debug(f"청크 {i+1}: 문장별 번역 (크기: {chunk_size})")
            translated = translate_chunk_by_sentences(chunk_text, source_lang)
        elif chunk_size > 1000:  # 큰 청크 - 분할 후 번역
            logger.debug(f"청크 {i+1}: 분할 번역 (크기: {chunk_size})")
            translated = translate_large_chunk_smart(chunk_text, source_lang)
        else:  # 중간 크기 - 일반 번역 (개선된 파라미터)
            logger.debug(f"청크 {i+1}: 일반 번역 (크기: {chunk_size})")
            translated = translate_chunk_optimized(chunk_text, source_lang)
        
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
    final_translation += f"\n\n---\n**번역 정보**\n- 번역 엔진: NLLB-200 (하이브리드 모드)\n- 소요 시간: {formatted_time}\n- 섹션 수: {len(chunks_info)}개\n---"
    
    logger.info(f"하이브리드 번역 완료: {len(chunks_info)}개 섹션, 소요 시간: {formatted_time}")
    return final_translation

def translate_chunk_by_sentences(text: str, source_lang: str = "auto") -> str:
    """작은 청크를 문장별로 번역"""
    sentences = split_text_into_sentences(text)
    translated_sentences = []
    
    for sentence in sentences:
        if sentence.strip():
            translated = translate_single_sentence(sentence.strip(), source_lang)
            translated_sentences.append(translated)
    
    return ' '.join(translated_sentences)

def translate_large_chunk_smart(text: str, source_lang: str = "auto") -> str:
    """큰 청크를 스마트하게 분할하여 번역"""
    # 문단 단위로 분할 (빈 줄 기준)
    paragraphs = re.split(r'\n\s*\n', text)
    translated_paragraphs = []
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            translated_paragraphs.append('')
            continue
            
        # 문단이 너무 긴 경우 문장별 번역
        if len(paragraph) > 500:
            translated = translate_chunk_by_sentences(paragraph, source_lang)
        else:
            translated = translate_chunk_optimized(paragraph, source_lang)
            
        translated_paragraphs.append(translated)
    
    return '\n\n'.join(translated_paragraphs)

def translate_chunk_optimized(text: str, source_lang: str = "auto") -> str:
    """중간 크기 청크를 최적화된 파라미터로 번역"""
    if not text.strip():
        return text
        
    translator = get_translator()
    
    try:
        # 언어 자동 감지
        if source_lang == "auto":
            source_lang = translator.detect_language(text)
            
        # NLLB 언어 코드로 변환
        src_code = NLLB_LANGUAGE_CODES.get(source_lang, 'eng_Latn')
        tgt_code = NLLB_LANGUAGE_CODES.get('ko', 'kor_Hang')
        
        # 이미 한국어인 경우
        if source_lang == 'ko':
            return text
        
        # 모델 초기화 확인
        if not translator._initialized or translator.translator is None:
            logger.error("NLLB 모델이 초기화되지 않았습니다.")
            return f"[번역 오류: 모델 초기화 실패]"
        
        # 전처리
        preprocessed_text = translator._preprocess_text(text)
        
        # 최적화된 번역
        result = translator.translator(
            preprocessed_text,
            src_lang=src_code,
            tgt_lang=tgt_code,
            max_length=min(len(preprocessed_text) * 2, 600),
            min_length=max(1, len(preprocessed_text) // 3),
            num_beams=3,
            do_sample=False,
            repetition_penalty=1.4,
            no_repeat_ngram_size=3,
            length_penalty=0.9,
            early_stopping=True
        )
        
        translated_text = result[0]['translation_text'] if isinstance(result, list) else result['translation_text']
        
        # 후처리
        cleaned_text = translator._postprocess_text(translated_text.strip())
        return cleaned_text
        
    except Exception as e:
        logger.error(f"청크 번역 실패: {e}")
        return f"[번역 오류: {str(e)}]"

def test_translator_initialization():
    """번역기 초기화 테스트"""
    try:
        logger.info("번역기 초기화 테스트 시작...")
        translator = get_translator()
        logger.info(f"번역기 인스턴스 생성됨: {translator}")
        logger.info(f"초기화 상태: {translator._initialized}")
        logger.info(f"모델 경로: {translator.model_name}")
        logger.info(f"디바이스: {translator.device}")
        
        if translator.translator is None:
            logger.error("translator.translator가 None입니다!")
            return False
        else:
            logger.info("translator.translator가 정상적으로 초기화되었습니다.")
            
        # 간단한 번역 테스트
        test_result = translator.translate_text("Hello", source_lang="en", target_lang="ko")
        logger.info(f"테스트 번역 결과: {test_result}")
        return True
        
    except Exception as e:
        logger.error(f"번역기 초기화 테스트 실패: {e}", exc_info=True)
        return False

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
        try:
            if hasattr(torch, 'cuda') and torch.cuda.is_available():
                torch.cuda.empty_cache()
        except AttributeError:
            logger.debug("CUDA 관련 함수를 찾을 수 없습니다.")
        
        logger.info("NLLB 번역기 리소스 정리 완료")

# 모듈 종료 시 자동 정리
import atexit
atexit.register(cleanup)