import requests
import yaml
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

# 프롬프트 템플릿 로드
PROMPT_FILE = Path('prompts/tax_translation_prompt.yaml')

with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
    PROMPTS = yaml.safe_load(f)

# 마크다운 분할 관련 상수 (저사양 환경에 최적화)
MAX_CHUNK_SIZE = 1000  # 최대 청크 크기를 줄임 (메모리 절약)
HEADER_PATTERN = re.compile(r'^(#{1,6}\s.+)')


def format_paragraph_prompt(text: str) -> str:
    """
    프롬프트 템플릿에 입력 텍스트를 삽입합니다.
    description과 template을 모두 포함합니다.
    """
    description = PROMPTS['paragraph_translation']['description']
    template = PROMPTS['paragraph_translation']['template']
    
    # description과 template을 합쳐서 전체 프롬프트 생성
    full_prompt = description + "\n\n" + template
    return full_prompt.replace('{{source_paragraph}}', text)


def split_markdown_by_headers(markdown_text: str) -> List[str]:
    """
    마크다운 텍스트를 헤더를 기준으로 분할합니다.
    너무 큰 청크는 추가로 분할하고, 너무 작은 청크는 합칩니다.
    """
    # 최소 청크 크기 더 줄임 (속도 최적화)
    MIN_CHUNK_SIZE = 200
    
    # 헤더 위치 찾기
    header_matches = list(HEADER_PATTERN.finditer(markdown_text))
    
    if not header_matches:
        # 헤더가 없으면 크기 기준으로 분할
        return split_text_by_size(markdown_text, MAX_CHUNK_SIZE)
    
    # 각 헤더 섹션의 정보 수집
    sections = []
    for i in range(len(header_matches)):
        current_match = header_matches[i]
        current_start = current_match.start()
        current_header = current_match.group(0)  # 헤더 텍스트
        current_level = len(current_header) - len(current_header.lstrip('#'))  # 헤더 레벨 (# 개수)
        
        # 다음 헤더의 시작 위치 또는 문서 끝
        next_start = header_matches[i+1].start() if i < len(header_matches) - 1 else len(markdown_text)
        
        # 현재 헤더부터 다음 헤더 전까지의 텍스트
        section_text = markdown_text[current_start:next_start]
        
        sections.append({
            'text': section_text,
            'level': current_level,
            'size': len(section_text),
            'start': current_start,
            'end': next_start
        })
    
    # 작은 섹션들을 합치기
    merged_sections = []
    current_merged = None
    
    for section in sections:
        if current_merged is None:
            current_merged = section.copy()
        elif section['size'] < MIN_CHUNK_SIZE and current_merged['size'] + section['size'] <= MAX_CHUNK_SIZE:
            # 현재 섹션이 작고, 합쳐도 최대 크기를 초과하지 않으면 합치기
            current_merged['text'] += section['text']
            current_merged['size'] += section['size']
            current_merged['end'] = section['end']
        else:
            # 현재 합쳐진 섹션을 추가하고 새로운 합본 시작
            merged_sections.append(current_merged)
            current_merged = section.copy()
    
    # 마지막 합본 추가
    if current_merged is not None:
        merged_sections.append(current_merged)
    
    # 최종 청크 생성
    chunks = []
    for section in merged_sections:
        # 섹션이 너무 크면 추가 분할
        if section['size'] > MAX_CHUNK_SIZE:
            sub_chunks = split_text_by_size(section['text'], MAX_CHUNK_SIZE)
            chunks.extend(sub_chunks)
        else:
            chunks.append(section['text'])
    
    return chunks


def split_text_by_size(text: str, max_size: int) -> List[str]:
    """
    텍스트를 지정된 최대 크기로 분할합니다.
    가능한 한 문단 경계에서 분할합니다.
    """
    if len(text) <= max_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_size
        
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # 문단 경계에서 분할 시도
        paragraph_end = text.rfind('\n\n', start, end)
        if paragraph_end != -1 and paragraph_end > start:
            end = paragraph_end + 2  # \n\n 포함
        else:
            # 문단 경계가 없으면 문장 경계에서 분할 시도
            sentence_end = max([text.rfind('. ', start, end), 
                               text.rfind('! ', start, end),
                               text.rfind('? ', start, end)])
            if sentence_end != -1 and sentence_end > start:
                end = sentence_end + 2  # 문장 구분자와 공백 포함
        
        chunks.append(text[start:end])
        start = end
    
    return chunks


def translate_markdown(markdown_text: str, path: str = None) -> str:
    """
    마크다운 텍스트를 헤더 기준으로 분할하여 번역합니다.
    path가 제공되면 번역 진행 상황을 progress_manager에 저장합니다.
    """
    print(f"\n[DEBUG] === 번역 과정 시작 ===\n")
    print(f"[DEBUG] 마크다운 문서 총 길이: {len(markdown_text)} 글자")
    print(f"[DEBUG] 경로: {path}")
    
    # 초기 헤더 기준 분할 전 헤더 수 확인
    header_matches = list(HEADER_PATTERN.finditer(markdown_text))
    print(f"[DEBUG] 총 헤더 수: {len(header_matches)}")
    
    # 헤더 레벨별 통계
    header_levels = {}
    for match in header_matches:
        header = match.group(0)
        level = len(header) - len(header.lstrip('#'))
        header_levels[level] = header_levels.get(level, 0) + 1
    
    print(f"[DEBUG] 헤더 레벨 통계: {header_levels}")
    
    # 분할 시작
    print(f"[DEBUG] 마크다운 분할 시작...")
    chunks = split_markdown_by_headers(markdown_text)
    
    # 청크 크기 통계
    chunk_sizes = [len(chunk) for chunk in chunks]
    avg_size = sum(chunk_sizes) / len(chunks) if chunks else 0
    max_size = max(chunk_sizes) if chunks else 0
    min_size = min(chunk_sizes) if chunks else 0
    
    print(f"[DEBUG] 분할 완료: 총 {len(chunks)}개 청크")
    print(f"[DEBUG] 청크 크기 - 평균: {avg_size:.1f}, 최대: {max_size}, 최소: {min_size}")
    print(f"[DEBUG] LLM API 호출 횟수: {len(chunks)}")
    
    # 각 청크의 길이 출력
    for i, size in enumerate(chunk_sizes):
        print(f"[DEBUG] 청크 {i+1}: {size} 글자 ({size/MAX_CHUNK_SIZE*100:.1f}% of MAX_CHUNK_SIZE)")
    
    # progress_manager에 청크 정보 저장
    if path:
        from progress_manager import progress_manager
        print(f"[DEBUG] progress_manager에 청크 정보 저장 시작 - 경로: {path}")
        
        # 각 청크의 정보 수집
        chunks_info = [
            {
                'index': i,
                'size': len(chunk),
                'status': 'pending',
                'preview': chunk[:50] + '...' if len(chunk) > 50 else chunk  # 미리보기
            } for i, chunk in enumerate(chunks)
        ]
        
        # 총 청크 수와 청크 정보 설정
        progress_manager.set_total_chunks(path, len(chunks), chunks_info)
        print(f"[DEBUG] progress_manager 청크 설정 완료: {len(chunks)}개")
    
    print(f"\n[DEBUG] === 번역 시작 ===\n")
    
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"[DEBUG] 청크 {i+1}/{len(chunks)} 번역 중 ({len(chunk)} 글자)...")
        
        # 현재 청크 진행 상황 업데이트
        if path:
            print(f"[DEBUG] progress_manager 청크 진행 업데이트: {i}")
            progress_manager.update_chunk_progress(path, i, 'processing')
        
        # 청크 번역
        translated = translate_chunk(chunk)
        translated_chunks.append(translated)
        
        # 번역 결과 저장
        if path:
            print(f"[DEBUG] progress_manager 청크 결과 추가: {i}")
            progress_manager.add_chunk_result(path, i, translated)
        
        print(f"[DEBUG] 청크 {i+1} 번역 완료")
    
    print(f"\n[DEBUG] === 번역 과정 완료 ===\n")
    return '\n'.join(translated_chunks)


def translate_chunk(text: str) -> str:
    """
    단일 청크를 번역합니다.
    추론 모드를 비활성화하고 CPU 환경에 최적화된 설정을 사용합니다.
    """
    prompt = format_paragraph_prompt(text)
    
    # CPU 환경에 최적화된 설정으로 추론 모드 비활성화
    import os
    cpu_cores = os.cpu_count() or 4  # CPU 코어 수 감지, 기본값 4
    
    data = {
        'model': 'qwen3:4b',
        'prompt': prompt,
        'stream': False,
        'system': "You are a direct translation assistant. Translate the given text from foreign language to Korean immediately without any thinking, reasoning, or explanation. Just provide the translation result only.",
        'options': {
            'temperature': 0.1,         # 낮은 온도로 일관된 결과
            'top_k': 5,                # 더 적은 토큰으로 빠른 결정 (10 → 5)
            'top_p': 0.2,              # 더 낮은 확률로 빠른 결정 (0.3 → 0.2)
            'repeat_penalty': 1.0,      # 반복 패널티 없음
            'num_predict': 4000,        # 응답 길이 줄임 (8000 → 4000)
            'stop': ['<think>', '<thinking>', '생각:', '추론:', '분석:', 'Let me think', 'I think', 'reasoning:', 'analysis:'],  # 추론 관련 단어에서 중단
            
            # CPU 최적화 설정 (속도 우선)
            'num_ctx': 1024,           # 컨텍스트 더 줄임 (2048 → 1024)
            'num_batch': 64,           # 배치 크기 더 줄임 (128 → 64)
            'num_gpu': 0,              # GPU 사용 안함
            'num_thread': cpu_cores,   # 모든 CPU 코어 사용 (속도 우선)
            
            # 메모리 최적화 설정
            'use_mmap': True,          # 메모리 매핑 사용 (필수)
            'use_mlock': False,        # 메모리 잠금 비활성화
            'f16_kv': False,           # CPU에서는 f32 사용 (더 안정적)
            'low_vram': True,          # 메모리 절약 모드 활성화
            
            # 성능 최적화 (속도 우선)
            'logits_all': False,       # 모든 로짓 반환 비활성화
            'vocab_only': False,       # 어휘만 사용 비활성화
            'embedding_only': False,   # 임베딩만 사용 비활성화
            'penalize_newline': False, # 개행 문자 패널티 비활성화
            
            # CPU 전용 최적화
            'numa': False,             # NUMA 최적화 비활성화 (단일 소켓용)
        }
    }
    
    try:
        import time
        start_time = time.time()
        
        print(f"Ollama API로 번역 요청 전송 중... ({len(prompt)} 글자)")
        print(f"[DEBUG] 속도 최적화 설정 적용됨 (스레드: {data['options']['num_thread']}, 청크크기: {len(text)})")
        
        # 단순한 POST 요청
        response = requests.post(
            'http://localhost:11434/api/generate',
            json=data,
            timeout=300  # 속도 우선으로 타임아웃 다시 줄임
        )
        
        response.raise_for_status()
        
        elapsed_time = time.time() - start_time
        print(f"[DEBUG] API 응답 시간: {elapsed_time:.2f}초")
        
        # 응답 내용 디버깅
        response_text = response.text
        print(f"[DEBUG] 원본 응답 길이: {len(response_text)} 글자")
        
        try:
            result = response.json()
            print(f"[DEBUG] JSON 파싱 성공. 키들: {list(result.keys())}")
            
            # 'response' 키 확인
            if 'response' in result:
                translated = result['response'].strip()
                
                # 추론 모드 텍스트가 포함되어 있는지 확인하고 제거
                thinking_patterns = [
                    r'<think>.*?</think>',
                    r'<thinking>.*?</thinking>',
                    r'생각:.*?(?=\n\n|\n[^생각])',
                    r'추론:.*?(?=\n\n|\n[^추론])',
                    r'분석:.*?(?=\n\n|\n[^분석])',
                    r'Let me think.*?(?=\n\n|\n[^L])',
                    r'I think.*?(?=\n\n|\n[^I])',
                    r'reasoning:.*?(?=\n\n|\n[^r])',
                    r'analysis:.*?(?=\n\n|\n[^a])'
                ]
                
                # 추론 텍스트 제거
                for pattern in thinking_patterns:
                    translated = re.sub(pattern, '', translated, flags=re.DOTALL | re.IGNORECASE)
                
                # 여러 개의 연속된 줄바꿈을 하나로 정리
                translated = re.sub(r'\n{3,}', '\n\n', translated).strip()
                
                if translated:
                    print(f"번역 완료: {len(translated)} 글자")
                    
                    # 추론 모드 텍스트가 남아있는지 체크
                    if any(keyword in translated.lower() for keyword in ['<think', 'let me think', '생각:', '추론:', '분석:']):
                        print("[WARNING] 응답에 추론 모드 텍스트가 포함되어 있을 수 있습니다.")
                        print(f"[WARNING] 응답 미리보기: {translated[:200]}...")
                    
                    return translated
                else:
                    print("[ERROR] 빈 응답 받음")
                    return "[ERROR] 빈 번역 결과"
            else:
                print(f"[ERROR] 'response' 키 없음. 사용 가능한 키: {list(result.keys())}")
                return f"[ERROR] API 응답에 'response' 키 없음"
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 파싱 실패: {e}")
            print(f"[ERROR] 응답 내용 (첫 500자): {response_text[:500]}")
            return f"[ERROR] JSON 파싱 실패"
        
    except requests.exceptions.Timeout:
        error_msg = "Ollama API 요청 시간 초과 (5분)"
        print(error_msg)
        return f"[ERROR] {error_msg}"
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama API 요청 오류: {str(e)}"
        print(error_msg)
        return f"[ERROR] {error_msg}"
    except Exception as e:
        error_msg = f"번역 중 예상치 못한 오류: {str(e)}"
        print(error_msg)
        return f"[ERROR] {error_msg}"


# 기존 함수 유지 (하위 호환성)
def translate_paragraph(text: str) -> str:
    """
    전체 텍스트를 한 번에 번역합니다.
    긴 문서의 경우 translate_markdown() 함수를 사용하는 것이 좋습니다.
    """
    print("경고: translate_paragraph()는 긴 문서에 적합하지 않습니다. translate_markdown() 사용을 권장합니다.")
    return translate_chunk(text)


def format_paragraph_prompt(text: str) -> str:
    """
    프롬프트 템플릿에 입력 텍스트를 삽입합니다.
    description과 template을 모두 포함합니다.
    """
    description = PROMPTS['paragraph_translation']['description']
    template = PROMPTS['paragraph_translation']['template']
    
    # description과 template을 합쳐서 전체 프롬프트 생성
    full_prompt = description + "\n\n" + template
    return full_prompt.replace('{{source_paragraph}}', text)


def split_markdown_by_headers(markdown_text: str) -> List[str]:
    """
    마크다운 텍스트를 헤더를 기준으로 분할합니다.
    너무 큰 청크는 추가로 분할하고, 너무 작은 청크는 합칩니다.
    """
    # 최소 청크 크기 (이 크기보다 작은 섹션은 다음 섹션과 합칩니다)
    MIN_CHUNK_SIZE = 500
    
    # 헤더 위치 찾기
    header_matches = list(HEADER_PATTERN.finditer(markdown_text))
    
    if not header_matches:
        # 헤더가 없으면 크기 기준으로 분할
        return split_text_by_size(markdown_text, MAX_CHUNK_SIZE)
    
    # 각 헤더 섹션의 정보 수집
    sections = []
    for i in range(len(header_matches)):
        current_match = header_matches[i]
        current_start = current_match.start()
        current_header = current_match.group(0)  # 헤더 텍스트
        current_level = len(current_header) - len(current_header.lstrip('#'))  # 헤더 레벨 (# 개수)
        
        # 다음 헤더의 시작 위치 또는 문서 끝
        next_start = header_matches[i+1].start() if i < len(header_matches) - 1 else len(markdown_text)
        
        # 현재 헤더부터 다음 헤더 전까지의 텍스트
        section_text = markdown_text[current_start:next_start]
        
        sections.append({
            'text': section_text,
            'level': current_level,
            'size': len(section_text),
            'start': current_start,
            'end': next_start
        })
    
    # 작은 섹션들을 합치기
    merged_sections = []
    current_merged = None
    
    for section in sections:
        if current_merged is None:
            current_merged = section.copy()
        elif section['size'] < MIN_CHUNK_SIZE and current_merged['size'] + section['size'] <= MAX_CHUNK_SIZE:
            # 현재 섹션이 작고, 합쳐도 최대 크기를 초과하지 않으면 합치기
            current_merged['text'] += section['text']
            current_merged['size'] += section['size']
            current_merged['end'] = section['end']
        else:
            # 현재 합쳐진 섹션을 추가하고 새로운 합본 시작
            merged_sections.append(current_merged)
            current_merged = section.copy()
    
    # 마지막 합본 추가
    if current_merged is not None:
        merged_sections.append(current_merged)
    
    # 최종 청크 생성
    chunks = []
    for section in merged_sections:
        # 섹션이 너무 크면 추가 분할
        if section['size'] > MAX_CHUNK_SIZE:
            sub_chunks = split_text_by_size(section['text'], MAX_CHUNK_SIZE)
            chunks.extend(sub_chunks)
        else:
            chunks.append(section['text'])
    
    return chunks


def split_text_by_size(text: str, max_size: int) -> List[str]:
    """
    텍스트를 지정된 최대 크기로 분할합니다.
    가능한 한 문단 경계에서 분할합니다.
    """
    if len(text) <= max_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_size
        
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # 문단 경계에서 분할 시도
        paragraph_end = text.rfind('\n\n', start, end)
        if paragraph_end != -1 and paragraph_end > start:
            end = paragraph_end + 2  # \n\n 포함
        else:
            # 문단 경계가 없으면 문장 경계에서 분할 시도
            sentence_end = max([text.rfind('. ', start, end), 
                               text.rfind('! ', start, end),
                               text.rfind('? ', start, end)])
            if sentence_end != -1 and sentence_end > start:
                end = sentence_end + 2  # 문장 구분자와 공백 포함
        
        chunks.append(text[start:end])
        start = end
    
    return chunks


def translate_markdown(markdown_text: str, path: str = None) -> str:
    """
    마크다운 텍스트를 헤더 기준으로 분할하여 번역합니다.
    path가 제공되면 번역 진행 상황을 progress_manager에 저장합니다.
    """
    print(f"\n[DEBUG] === 번역 과정 시작 ===\n")
    print(f"[DEBUG] 마크다운 문서 총 길이: {len(markdown_text)} 글자")
    print(f"[DEBUG] 경로: {path}")
    
    # 초기 헤더 기준 분할 전 헤더 수 확인
    header_matches = list(HEADER_PATTERN.finditer(markdown_text))
    print(f"[DEBUG] 총 헤더 수: {len(header_matches)}")
    
    # 헤더 레벨별 통계
    header_levels = {}
    for match in header_matches:
        header = match.group(0)
        level = len(header) - len(header.lstrip('#'))
        header_levels[level] = header_levels.get(level, 0) + 1
    
    print(f"[DEBUG] 헤더 레벨 통계: {header_levels}")
    
    # 분할 시작
    print(f"[DEBUG] 마크다운 분할 시작...")
    chunks = split_markdown_by_headers(markdown_text)
    
    # 청크 크기 통계
    chunk_sizes = [len(chunk) for chunk in chunks]
    avg_size = sum(chunk_sizes) / len(chunks) if chunks else 0
    max_size = max(chunk_sizes) if chunks else 0
    min_size = min(chunk_sizes) if chunks else 0
    
    print(f"[DEBUG] 분할 완료: 총 {len(chunks)}개 청크")
    print(f"[DEBUG] 청크 크기 - 평균: {avg_size:.1f}, 최대: {max_size}, 최소: {min_size}")
    print(f"[DEBUG] LLM API 호출 횟수: {len(chunks)}")
    
    # 각 청크의 길이 출력
    for i, size in enumerate(chunk_sizes):
        print(f"[DEBUG] 청크 {i+1}: {size} 글자 ({size/MAX_CHUNK_SIZE*100:.1f}% of MAX_CHUNK_SIZE)")
    
    # progress_manager에 청크 정보 저장
    if path:
        from progress_manager import progress_manager
        print(f"[DEBUG] progress_manager에 청크 정보 저장 시작 - 경로: {path}")
        
        # 각 청크의 정보 수집
        chunks_info = [
            {
                'index': i,
                'size': len(chunk),
                'status': 'pending',
                'preview': chunk[:50] + '...' if len(chunk) > 50 else chunk  # 미리보기
            } for i, chunk in enumerate(chunks)
        ]
        
        # 총 청크 수와 청크 정보 설정
        progress_manager.set_total_chunks(path, len(chunks), chunks_info)
        print(f"[DEBUG] progress_manager 청크 설정 완료: {len(chunks)}개")
    
    print(f"\n[DEBUG] === 번역 시작 ===\n")
    
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"[DEBUG] 청크 {i+1}/{len(chunks)} 번역 중 ({len(chunk)} 글자)...")
        
        # 현재 청크 진행 상황 업데이트
        if path:
            print(f"[DEBUG] progress_manager 청크 진행 업데이트: {i}")
            progress_manager.update_chunk_progress(path, i, 'processing')
        
        # 청크 번역
        translated = translate_chunk(chunk)
        translated_chunks.append(translated)
        
        # 번역 결과 저장
        if path:
            print(f"[DEBUG] progress_manager 청크 결과 추가: {i}")
            progress_manager.add_chunk_result(path, i, translated)
        
        print(f"[DEBUG] 청크 {i+1} 번역 완료")
    
    print(f"\n[DEBUG] === 번역 과정 완료 ===\n")
    return '\n'.join(translated_chunks)


def translate_chunk(text: str) -> str:
    """
    단일 청크를 번역합니다.
    추론 모드를 비활성화하고 CPU 환경에 최적화된 설정을 사용합니다.
    """
    prompt = format_paragraph_prompt(text)
    
    # CPU 환경에 최적화된 설정으로 추론 모드 비활성화
    import os
    cpu_cores = os.cpu_count() or 4  # CPU 코어 수 감지, 기본값 4
    
    data = {
        'model': 'qwen3:4b',
        'prompt': prompt,
        'stream': False,
        'system': "You are a direct translation assistant. Translate the given text from foreign language to Korean immediately without any thinking, reasoning, or explanation. Just provide the translation result only.",
        'options': {
            'temperature': 0.1,         # 낮은 온도로 일관된 결과
            'top_k': 10,               # 상위 10개 토큰만 고려
            'top_p': 0.3,              # 누적 확률 30%로 제한
            'repeat_penalty': 1.0,      # 반복 패널티 없음
            'num_predict': 8000,        # 충분한 응답 길이
            'stop': ['<think>', '<thinking>', '생각:', '추론:', '분석:', 'Let me think', 'I think', 'reasoning:', 'analysis:'],  # 추론 관련 단어에서 중단
            
            # CPU 최적화 설정
            'num_ctx': 2048,           # 컨텍스트 길이 줄임 (메모리 절약)
            'num_batch': 128,          # 배치 크기 줄임 (메모리 절약)
            'num_gpu': 0,              # GPU 사용 안함
            'num_thread': max(1, cpu_cores - 1),  # CPU 코어 수 - 1 (시스템 여유분 확보)
            
            # 메모리 최적화 설정
            'use_mmap': True,          # 메모리 매핑 사용 (필수)
            'use_mlock': False,        # 메모리 잠금 비활성화
            'f16_kv': False,           # CPU에서는 f32 사용 (더 안정적)
            'low_vram': True,          # 메모리 절약 모드 활성화
            
            # 성능 최적화
            'logits_all': False,       # 모든 로짓 반환 비활성화
            'vocab_only': False,       # 어휘만 사용 비활성화
            'embedding_only': False,   # 임베딩만 사용 비활성화
            'penalize_newline': False, # 개행 문자 패널티 비활성화
            
            # CPU 전용 최적화
            'numa': False,             # NUMA 최적화 비활성화 (단일 소켓용)
        }
    }
    
    try:
        print(f"Ollama API로 번역 요청 전송 중... ({len(prompt)} 글자)")
        print(f"[DEBUG] 추론 모드 비활성화 설정 적용됨")
        
        # 단순한 POST 요청
        response = requests.post(
            'http://localhost:11434/api/generate',
            json=data,
            timeout=300  # 5분 타임아웃
        )
        
        response.raise_for_status()
        
        # 응답 내용 디버깅
        response_text = response.text
        print(f"[DEBUG] 원본 응답 길이: {len(response_text)} 글자")
        
        try:
            result = response.json()
            print(f"[DEBUG] JSON 파싱 성공. 키들: {list(result.keys())}")
            
            # 'response' 키 확인
            if 'response' in result:
                translated = result['response'].strip()
                
                # 추론 모드 텍스트가 포함되어 있는지 확인하고 제거
                thinking_patterns = [
                    r'<think>.*?</think>',
                    r'<thinking>.*?</thinking>',
                    r'생각:.*?(?=\n\n|\n[^생각])',
                    r'추론:.*?(?=\n\n|\n[^추론])',
                    r'분석:.*?(?=\n\n|\n[^분석])',
                    r'Let me think.*?(?=\n\n|\n[^L])',
                    r'I think.*?(?=\n\n|\n[^I])',
                    r'reasoning:.*?(?=\n\n|\n[^r])',
                    r'analysis:.*?(?=\n\n|\n[^a])'
                ]
                
                # 추론 텍스트 제거
                for pattern in thinking_patterns:
                    translated = re.sub(pattern, '', translated, flags=re.DOTALL | re.IGNORECASE)
                
                # 여러 개의 연속된 줄바꿈을 하나로 정리
                translated = re.sub(r'\n{3,}', '\n\n', translated).strip()
                
                if translated:
                    print(f"번역 완료: {len(translated)} 글자")
                    
                    # 추론 모드 텍스트가 남아있는지 체크
                    if any(keyword in translated.lower() for keyword in ['<think', 'let me think', '생각:', '추론:', '분석:']):
                        print("[WARNING] 응답에 추론 모드 텍스트가 포함되어 있을 수 있습니다.")
                        print(f"[WARNING] 응답 미리보기: {translated[:200]}...")
                    
                    return translated
                else:
                    print("[ERROR] 빈 응답 받음")
                    return "[ERROR] 빈 번역 결과"
            else:
                print(f"[ERROR] 'response' 키 없음. 사용 가능한 키: {list(result.keys())}")
                return f"[ERROR] API 응답에 'response' 키 없음"
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 파싱 실패: {e}")
            print(f"[ERROR] 응답 내용 (첫 500자): {response_text[:500]}")
            return f"[ERROR] JSON 파싱 실패"
        
    except requests.exceptions.Timeout:
        error_msg = "Ollama API 요청 시간 초과 (5분)"
        print(error_msg)
        return f"[ERROR] {error_msg}"
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama API 요청 오류: {str(e)}"
        print(error_msg)
        return f"[ERROR] {error_msg}"
    except Exception as e:
        error_msg = f"번역 중 예상치 못한 오류: {str(e)}"
        print(error_msg)
        return f"[ERROR] {error_msg}"


# 기존 함수 유지 (하위 호환성)
def translate_paragraph(text: str) -> str:
    """
    전체 텍스트를 한 번에 번역합니다.
    긴 문서의 경우 translate_markdown() 함수를 사용하는 것이 좋습니다.
    """
    print("경고: translate_paragraph()는 긴 문서에 적합하지 않습니다. translate_markdown() 사용을 권장합니다.")
    return translate_chunk(text)