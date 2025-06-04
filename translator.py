import requests
import yaml
import re
import json
from pathlib import Path
from typing import List
import time
import os

s = requests.Session() # Global session for TCP connection reuse

"""문서 번역에 사용되는 도구 함수 모음."""

PROMPT_FILE = Path('prompts/tax_translation_prompt.yaml')

with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
    PROMPTS = yaml.safe_load(f)

MAX_CHUNK_SIZE = 1000
HEADER_PATTERN = re.compile(r'^(#{1,6}\s.+)')


def format_paragraph_prompt(text: str) -> str:
    """프롬프트 템플릿에 입력 텍스트를 삽입한다."""
    description = PROMPTS['paragraph_translation']['description']
    template = PROMPTS['paragraph_translation']['template']
    full_prompt = description + "\n\n" + template
    return full_prompt.replace('{{source_paragraph}}', text)


def split_text_by_size(text: str, max_size: int) -> List[str]:
    """텍스트를 최대 크기에 맞게 분할한다."""
    if len(text) <= max_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_size
        if end >= len(text):
            chunks.append(text[start:])
            break

        # 가능하면 문단이나 문장 경계에서 자른다
        paragraph_end = text.rfind('\n\n', start, end)
        if paragraph_end != -1 and paragraph_end > start:
            end = paragraph_end + 2
        else:
            sentence_end = max([
                text.rfind('. ', start, end),
                text.rfind('! ', start, end),
                text.rfind('? ', start, end)
            ])
            if sentence_end != -1 and sentence_end > start:
                end = sentence_end + 2
        chunks.append(text[start:end])
        start = end
    return chunks


def split_markdown_by_headers(markdown_text: str) -> List[str]:
    """마크다운 텍스트를 헤더 단위로 분할한다."""
    # 이 크기보다 작은 섹션은 다음 섹션과 합친다
    MIN_CHUNK_SIZE = 500
    # 헤더 위치 찾기
    header_matches = list(HEADER_PATTERN.finditer(markdown_text))
    if not header_matches:
        # 헤더가 없으면 길이 기준으로 분할
        return split_text_by_size(markdown_text, MAX_CHUNK_SIZE)

    # 각 헤더 구간의 정보를 저장
    sections = []
    for i, match in enumerate(header_matches):
        current_start = match.start()
        current_header = match.group(0)
        current_level = len(current_header) - len(current_header.lstrip('#'))
        next_start = header_matches[i+1].start() if i < len(header_matches) - 1 else len(markdown_text)
        section_text = markdown_text[current_start:next_start]
        sections.append({
            'text': section_text,
            'level': current_level,
            'size': len(section_text),
            'start': current_start,
            'end': next_start,
        })

    # 너무 작은 섹션은 앞부분과 합친다
    merged_sections = []
    current = None
    for section in sections:
        if current is None:
            current = section.copy()
        elif section['size'] < MIN_CHUNK_SIZE and current['size'] + section['size'] <= MAX_CHUNK_SIZE:
            current['text'] += section['text']
            current['size'] += section['size']
            current['end'] = section['end']
        else:
            merged_sections.append(current)
            current = section.copy()
    if current is not None:
        merged_sections.append(current)

    chunks = []
    for section in merged_sections:
        if section['size'] > MAX_CHUNK_SIZE:
            chunks.extend(split_text_by_size(section['text'], MAX_CHUNK_SIZE))
        else:
            chunks.append(section['text'])
    return chunks


def translate_chunk(text: str, idx: int | None = None, total: int | None = None) -> str:
    """단일 청크를 번역한다."""
    prompt = format_paragraph_prompt(text)
    prompt += " /no_think"  # 안전장치 추가

    if idx is not None and total is not None:
        # 프롬프트가 매우 길 수 있으므로, 일부만 로깅하거나 DEBUG 레벨로 로깅하는 것을 고려
        print(f"[DEBUG] LLM 호출 프롬프트 {idx}/{total} (일부): {prompt[:200]}...")
    else:
        print(f"[DEBUG] LLM 호출 프롬프트 (일부): {prompt[:200]}...")
    
    # 로컬 import os 및 cpu_cores 계산은 제거됨 (os는 전역으로 임포트, cpu_cores는 단순화된 옵션에서 불필요)

    data = {
        'model': 'qwen3:4b', 
        'prompt': prompt,
        'stream': True,      # 스트리밍 활성화
        'system': "/no_think You are a direct translation assistant. Translate the given text from foreign language to Korean immediately without any thinking, reasoning, or explanation. Just provide the translation result only.", # 시스템 프롬프트 유지
        'options': {
            'temperature': 0.1,    # 기존 온도 설정 유지
            'enable_thinking': False # '생각 없는' 번역 활성화
            # 다른 상세 옵션들은 Ollama 기본값을 사용하도록 제거.
            # 필요시 여기에 'num_gpu', 'num_thread': max(1, (os.cpu_count() or 4) -1) 등 추가 가능
        }
    }

    try:
        response = s.post(  # s.post() 사용
            'http://localhost:11434/api/generate',
            json=data,
            stream=True, # stream=True 명시
            timeout=300 
        )
        response.raise_for_status()

        translated_parts = []
        for line in response.iter_lines(decode_unicode=True):
            if line: 
                # print(f"[DEBUG] Ollama API raw line: {line}") 
                try:
                    chunk_data = json.loads(line)
                    if "response" in chunk_data:
                        translated_parts.append(chunk_data["response"])
                    if chunk_data.get("done"):
                        if chunk_data.get("total_duration"):
                            print(f"[INFO] Ollama 스트리밍 완료. 총 소요시간: {chunk_data.get('total_duration')/1e9:.2f}초, 처리 토큰 수: {chunk_data.get('eval_count')}")
                        else:
                            print(f"[INFO] Ollama 스트리밍 완료 (세부 정보 없음).")
                        break # 스트림의 끝을 나타내면 루프 종료
                except json.JSONDecodeError:
                    print(f"[ERROR] Ollama 응답라인 JSON 파싱 오류: '{line}'")
                except Exception as e_parse: 
                    print(f"[ERROR] Ollama 응답라인 처리 중 오류: '{line}', 오류: {e_parse}")
        
        translated = "".join(translated_parts)
        
        # 기존의 '생각' 패턴 제거 로직은 예비용으로 유지
        # print(f"[DEBUG] Translated content before cleaning: '{translated}'") 
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
        for pattern in thinking_patterns:
            translated = re.sub(pattern, '', translated, flags=re.DOTALL | re.IGNORECASE)
        translated = re.sub(r'\n{3,}', '\n\n', translated).strip()
        # print(f"[DEBUG] Translated content after cleaning: '{translated}'")
        return translated if translated else "[ERROR] 빈 번역 결과"
    except requests.exceptions.Timeout:
        return "[ERROR] Ollama API 요청 시간 초과 (5분)"
    except requests.exceptions.RequestException as e:
        return f"[ERROR] Ollama API 요청 오류: {str(e)}"
    except Exception as e:
        return f"[ERROR] 번역 중 예상치 못한 오류: {str(e)}"


def translate_markdown(markdown_text: str, path: str | None = None) -> str:
    """마크다운 문서를 번역한다."""
    start_time = time.time()
    chunks = split_markdown_by_headers(markdown_text)
    print(f"[DEBUG] 총 {len(chunks)}개 청크로 분할됨")

    if path:
        from progress_manager import progress_manager
        chunks_info = [
            {
                'index': i,
                'size': len(chunk),
                'status': 'pending',
                'preview': chunk[:50] + '...' if len(chunk) > 50 else chunk
            } for i, chunk in enumerate(chunks)
        ]
        progress_manager.set_total_chunks(path, len(chunks), chunks_info)

    translated_chunks: List[str] = []
    for i, chunk in enumerate(chunks):
        if path:
            progress_manager.update_chunk_progress(path, i, 'processing')
        translated = translate_chunk(chunk, i + 1, len(chunks))
        translated_chunks.append(translated)
        if path:
            progress_manager.add_chunk_result(path, i, translated)

    end_time = time.time()
    elapsed_time = end_time - start_time
    formatted_time = f"{elapsed_time:.2f} 초"

    final_translation = '\n'.join(translated_chunks)
    final_translation += f"\n\n--- 번역 소요 시간: {formatted_time} ---"
    return final_translation


def translate_paragraph(text: str) -> str:
    """이전 버전 호환을 위한 단순 래퍼."""
    print("경고: translate_paragraph()는 긴 문서에 적합하지 않습니다. translate_markdown() 사용을 권장합니다.")
    return translate_chunk(text)

