import requests
import yaml
from pathlib import Path

PROMPT_FILE = Path('prompts/tax_translation_prompt.yaml')

with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
    PROMPTS = yaml.safe_load(f)


def format_paragraph_prompt(text: str) -> str:
    template = PROMPTS['paragraph_translation']['template']
    return template.replace('{{source_paragraph}}', text)


def translate_paragraph(text: str) -> str:
    prompt = format_paragraph_prompt(text)
    data = {
        'model': 'exaone3.5:2.4b',
        'prompt': prompt,
    }
    try:
        res = requests.post('http://localhost:11434/api/generate', json=data, timeout=60)
        res.raise_for_status()
        return res.json().get('response', '').strip()
    except Exception:
        return ''
