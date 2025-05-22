# from docling.document_converter import DocumentConverter  # 실제 환경에 맞게 경로 조정 필요
import os
from docling.document_converter import DocumentConverter

SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt']

def convert_to_markdown(input_path, output_md_path=None):
    """
    파일 경로를 받아 DocumentConverter를 이용해 마크다운 파일로 변환합니다.
    output_md_path가 지정되지 않으면 입력 파일명에 .md 확장자를 붙여 저장합니다.
    """

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"입력 파일이 존재하지 않습니다: {input_path}")

    if output_md_path is None:
        base, _ = os.path.splitext(input_path)
        output_md_path = base + ".md"

    converter = DocumentConverter()
    result = converter.convert(input_path)
    markdown = result.document.export_to_markdown()
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    return output_md_path

# 사용 예시:
# md_path = convert_to_markdown("sample.pdf")
# print(f"마크다운 파일로 변환 완료: {md_path}")

import yaml
import requests
import json

def load_restore_markdown_prompt(markdown_text):
    """
    restore_markdown_prompt.yaml에서 description, template을 읽어 실제 프롬프트 문자열을 생성
    """
    yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompt", "restore_markdown_prompt.yaml"))
    with open(yaml_path, 'r', encoding='utf-8') as f:
        prompts = yaml.safe_load(f)
    desc = prompts['restore_markdown']['description'].strip()
    template = prompts['restore_markdown']['template'].replace('{{markdown_text}}', markdown_text)
    return desc + "\n\n" + template

def call_ollama_llm(prompt, model='gemma3:4b', top_k=40):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "options": {"top_k": top_k}},
            stream=True
        )
        lines = response.iter_lines(decode_unicode=True)
        result = ""
        for line in lines:
            try:
                data = json.loads(line)
                if "response" in data:
                    result += data["response"]
            except Exception as e:
                print("[Ollama 응답 파싱 오류]", e)
        return result.strip()
    except Exception as e:
        print(f"Ollama 응답 오류: {e}")
        return ""

def generate_clean_markdown(input_path, revised_md_path=None):
    """
    1. 입력 파일을 마크다운(.md)으로 변환
    2. 변환된 마크다운을 LLM을 통해 구조 복원(클린업)
    3. 수정된 마크다운을 별도 파일로 저장 (기본: <입력파일명>_revised.md)
    4. 수정된 마크다운 파일 경로 반환
    """
    # 1. 원본 마크다운 생성
    md_path = convert_to_markdown(input_path)
    with open(md_path, "r", encoding="utf-8") as f:
        markdown = f.read()
    # 2. LLM 프롬프트 생성 및 호출
    prompt = load_restore_markdown_prompt(markdown)
    revised_markdown = call_ollama_llm(prompt, model="gemma3:4b")
    # 3. 결과 저장
    if revised_md_path is None:
        base, _ = os.path.splitext(md_path)
        revised_md_path = base + "_revised.md"
    with open(revised_md_path, "w", encoding="utf-8") as f:
        f.write(revised_markdown)
    return revised_md_path
