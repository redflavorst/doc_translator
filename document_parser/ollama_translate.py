import requests
import json
import yaml
import os
import logging

# 로거 설정
logger = logging.getLogger(__name__)
s = requests.Session() # Global session for TCP connection reuse

def load_prompt(template_key, **kwargs):
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompt', 'tax_translation_prompt.yaml')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompts = yaml.safe_load(f)
    description = prompts[template_key].get('description', '')
    template = prompts[template_key]['template']
    # description과 template을 합쳐서 프롬프트 생성
    merged_prompt = description.strip() + "\n" + template.strip()
    merged_prompt = merged_prompt.replace('{{source_sentence}}', kwargs.get('source_sentence', ''))
    merged_prompt = merged_prompt.replace('{{source_paragraph}}', kwargs.get('source_paragraph', ''))
    return merged_prompt


def translate_with_ollama(text, model='qwen3:4b'):
    prompt = load_prompt('paragraph_translation', source_paragraph=text)
    prompt += " /no_think"  # 안전장치 추가
    logger.info(f"[Ollama 호출 준비] 모델: {model}") # top_k 제거됨
    # 프롬프트가 매우 길 수 있으므로, 일부만 로깅하거나 DEBUG 레벨로 로깅하는 것을 고려
    logger.info(f"[Ollama 프롬프트 일부] {prompt[:200]}...") 

    request_payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,  # 스트리밍 활성화
        "options": {
            "enable_thinking": False # top_k 제거, Ollama 기본값 사용
        }
    }
    logger.debug(f"Ollama 요청 페이로드: {json.dumps(request_payload, ensure_ascii=False)}")

    try:
        logger.info(f"Ollama API 요청 시작: http://localhost:11434/api/generate, 모델: {model}")
        response = s.post( # 세션 사용 및 stream=True로 변경
            "http://localhost:11434/api/generate",
            json=request_payload,
            stream=True,
            timeout=300  # 300초 타임아웃 설정
        )
        logger.info(f"[Ollama 응답코드] {response.status_code}")
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        lines = response.iter_lines(decode_unicode=True)
        result = ""
        for line in lines:
            logger.debug(f"[Ollama 응답라인] {line}")
            try:
                data = json.loads(line)
                if "response" in data:
                    result += data["response"]
                if data.get("done"):
                    if data.get("total_duration"):
                        logger.info(f"Ollama 스트리밍 완료. 총 소요시간: {data.get('total_duration')/1e9:.2f}초, 처리 토큰 수: {data.get('eval_count')}")
                    else:
                        logger.info(f"Ollama 스트리밍 완료 (세부 정보 없음).")

            except json.JSONDecodeError as e:
                logger.error(f"[Ollama 응답라인 JSON 파싱 오류] 데이터: '{line}', 오류: {e}")
            except Exception as e:
                logger.error(f"[Ollama 응답라인 처리 중 알 수 없는 오류] 데이터: '{line}', 오류: {e}")
        
        logger.info(f"[Ollama 최종 번역 결과 일부] {result.strip()[:200]}...")
        # logger.debug(f"[Ollama 최종 번역 결과 전체] {result.strip()}") # 전체 결과는 DEBUG로
        return result.strip()

    except requests.exceptions.HTTPError as e:
        logger.error(f"Ollama API HTTP 오류: {e.status_code} {e.response.reason if e.response else ''}")
        logger.error(f"응답 내용: {e.response.text if e.response else 'N/A'}")
        logger.error(f"요청 모델: {model}, 사용 가능한 모델 확인: curl http://localhost:11434/api/tags")
        return ""
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Ollama API 연결 오류: {e}")
        logger.error(f"Ollama 서버(http://localhost:11434)가 실행 중이고 접근 가능한지 확인하세요.")
        logger.error(f"사용하려는 모델 '{model}'이 Ollama에 pull 되어 있는지도 확인하세요. (사용 가능 모델 확인: curl http://localhost:11434/api/tags)")
        return ""
    except requests.exceptions.Timeout as e:
        logger.error(f"Ollama API 타임아웃 오류: {e}")
        return ""
    except Exception as e:
        logger.error(f"Ollama 번역 중 알 수 없는 오류: {e}", exc_info=True)
        return ""