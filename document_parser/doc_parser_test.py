import os
import re
import yaml
import json
import requests
from docling.document_converter import DocumentConverter

def convert_pdf_to_markdown(pdf_path):
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    return result.document.export_to_markdown()

def split_markdown_by_headers(markdown_text, level=2):
    """Split markdown into blocks that include each header and its following body.

    If text exists before the first header, include it as the first block.
    """
    pattern = re.compile(rf'^(#{{1,{level}}})\s+.*', re.MULTILINE)
    indices = [m.start() for m in pattern.finditer(markdown_text)]

    # Include preface before the first header, if any
    if not indices or indices[0] != 0:
        indices.insert(0, 0)

    indices.append(len(markdown_text))

    blocks = [markdown_text[indices[i]:indices[i + 1]].strip()
              for i in range(len(indices) - 1)]
    return blocks

def count_tokens(text):
    """Rudimentary token count based on whitespace and punctuation."""
    tokens = re.findall(r'\w+|[^\w\s]', text, re.UNICODE)
    return len(tokens)

def group_blocks_by_token_limit(blocks, token_limit=500):
    grouped = []
    current_group = []
    current_tokens = 0

    for block in blocks:
        token_count = count_tokens(block)
        if current_tokens + token_count > token_limit and current_group:
            grouped.append('\n\n'.join(current_group))
            current_group = []
            current_tokens = 0
        current_group.append(block)
        current_tokens += token_count

    if current_group:
        grouped.append('\n\n'.join(current_group))

    return grouped

def group_blocks_by_word_limit(blocks, word_limit=1000):
    grouped = []
    current_group = []
    current_word_count = 0

    for block in blocks:
        word_count = len(re.findall(r'\w+', block))
        if current_word_count + word_count > word_limit and current_group:
            grouped.append('\n\n'.join(current_group))
            current_group = []
            current_word_count = 0
        current_group.append(block)
        current_word_count += word_count

    if current_group:
        grouped.append('\n\n'.join(current_group))

    return grouped

def load_restore_markdown_prompt(block_text, yaml_path="../prompt/restore_markdown_prompt.yaml"):
    with open(yaml_path, 'r', encoding='utf-8') as f:
        prompts = yaml.safe_load(f)
    desc = prompts['restore_markdown']['description'].strip()
    template = prompts['restore_markdown']['template'].replace('{{markdown_text}}', block_text)
    return desc + "\n\n" + template

def call_ollama_llm(prompt, model='qwen3:4b'):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "options": {
                    "num_predict": 2048,
                    "temperature": 0.2
                }
            }
        )
        result = ""
        for line in response.text.strip().splitlines():
            try:
                data = json.loads(line)
                result += data.get("response", "")
            except Exception as e:
                print("[라인 파싱 오류]", e, line)
        return result.strip()
    except Exception as e:
        print(f"[Ollama 오류] {e}")
        return ""

def process_pdf_structured_grouped(pdf_path, output_dir="output_groups", token_limit=500):
    os.makedirs(output_dir, exist_ok=True)

    print("[STEP 1] PDF → 마크다운 변환 중...")
    markdown = convert_pdf_to_markdown(pdf_path)
    with open(os.path.join(output_dir, "original.md"), "w", encoding="utf-8") as f:
        f.write(markdown)

    print("[STEP 2] 마크다운 → 헤더 단위 분할 중...")
    blocks = split_markdown_by_headers(markdown, level=2)

    print(f"[STEP 3] 토큰 기준 {token_limit} 이하로 블록 묶는 중...")
    grouped_blocks = group_blocks_by_token_limit(blocks, token_limit=token_limit)

    merged_output = ""
    for i, group in enumerate(grouped_blocks):
        print(f"[STEP 4-{i+1}] 블록 그룹 {i+1}/{len(grouped_blocks)} 구조 복원 중...")
        prompt = load_restore_markdown_prompt(group)
        print("\n=== 프롬프트 시작 ===\n")
        print(prompt)
        print("\n=== 프롬프트 끝 ===\n")
        restored = call_ollama_llm(prompt)

        group_path = os.path.join(output_dir, f"group_{i+1:02d}.md")
        with open(group_path, "w", encoding="utf-8") as f:
            f.write(restored)

        merged_output += restored + "\n\n"

    final_path = os.path.join(output_dir, "final_revised.md")
    with open(final_path, "w", encoding="utf-8") as f:
        f.write(merged_output)

    print(f"[✅ 완료] 최종 복원된 문서가 {final_path}에 저장되었습니다.")

# 사용 예:
# process_pdf_structured_grouped("your_document.pdf", token_limit=500)

if __name__ == "__main__":
    process_pdf_structured_grouped("../data/jp_keiyakusyo3sya.pdf", token_limit=500)
