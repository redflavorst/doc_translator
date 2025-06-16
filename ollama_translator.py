#!/usr/bin/env python3
"""
다국어 문서 번역기 (→ 한국어)
- 경량 LLM 모델(Ollama 등) 사용
- pymupdf4llm을 활용한 PDF → Markdown 변환
- Markdown 구조 보존 번역 지원
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Tuple
from progress_manager import progress_manager
from argos_translator import MarkdownTranslator, TranslationUnit


class SupportedLanguage(Enum):
    ENGLISH = "en"
    JAPANESE = "ja"
    CHINESE = "zh"
    KOREAN = "ko"
    AUTO = "auto"


class LLMProvider(Enum):
    OLLAMA = "ollama"


@dataclass
class TranslationConfig:
    model_name: str = "gemma3:4b"
    provider: LLMProvider = LLMProvider.OLLAMA
    source_lang: SupportedLanguage = SupportedLanguage.AUTO
    target_lang: SupportedLanguage = SupportedLanguage.KOREAN
    temperature: float = 0.1
    max_tokens: int = 1024


def pdf_to_markdown(pdf_path: str) -> str:
    """pymupdf4llm을 사용하여 PDF를 Markdown 텍스트로 변환"""
    try:
        import pymupdf4llm
        return pymupdf4llm.to_markdown(pdf_path)
    except ImportError as e:
        raise RuntimeError("pymupdf4llm 패키지가 필요합니다") from e


class MarkdownPreserver:
    """Markdown 포맷을 보존하기 위한 유틸"""

    def __init__(self) -> None:
        self.patterns = [
            (r'(\*\*[^*\n]+\*\*)', 'BOLD'),
            (r'(\*[^*\n]+\*)', 'ITALIC'),
            (r'(`[^`\n]+`)', 'CODE'),
            (r'(```[\s\S]*?```)', 'CODEBLOCK'),
        ]

    def extract(self, text: str) -> List[Tuple[str, str]]:
        elements: List[Tuple[str, str]] = []
        for idx, (pattern, _) in enumerate(self.patterns):
            for m in re.finditer(pattern, text, re.MULTILINE):
                placeholder = f"__MD_{idx}_{len(elements)}__"
                elements.append((placeholder, m.group(1)))
                text = text.replace(m.group(1), placeholder, 1)
        return elements, text

    def restore(self, text: str, elements: List[Tuple[str, str]]) -> str:
        for placeholder, original in elements:
            text = text.replace(placeholder, original)
        return text


class MultilingualTranslator:
    def __init__(self, config: TranslationConfig) -> None:
        self.config = config
        self.preserver = MarkdownPreserver()
        self.client = None
        if config.provider == LLMProvider.OLLAMA:
            self._init_ollama()

    def _init_ollama(self) -> None:
        try:
            import ollama
            self.client = ollama
        except ImportError as e:
            raise RuntimeError("ollama 패키지가 필요합니다") from e

    def _prompt(self, text: str, source: str) -> str:
        return (
            f"다음 {source} 텍스트를 한국어로 번역하세요.\n\n"
            f"원문: {text}\n\n번역:"
        )

    def translate_unit(self, text: str, source_lang: str) -> str:
        elements, clean = self.preserver.extract(text)
        prompt = self._prompt(clean, source_lang)
        try:
            response = self.client.chat(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": self.config.temperature, "num_predict": self.config.max_tokens},
                stream=False,
            )
            result = response["message"]["content"].strip()
        except Exception:
            result = text
        translated = self.preserver.restore(result, elements)
        return translated

    def translate_markdown(self, markdown: str, source_lang: str, path: str = None) -> str:
        # Argos 방식과 동일하게 units 분할
        translator = MarkdownTranslator(source_lang, "ko")
        units = translator.split_into_units(markdown)
        results: List[str] = []
        total_chunks = len(units)
        # 각 청크 정보 구성 (chunk index, type, size, status)
        chunks_info = [
            {"index": i, "type": unit.unit_type, "size": len(unit.content), "status": "pending"}
            for i, unit in enumerate(units)
        ]
        if path:
            progress_manager.set_total_chunks(path, total_chunks, chunks_info)
        try:
            for idx, unit in enumerate(units):
                if path:
                    progress_manager.update_chunk_progress(path, idx, "processing")
                if not unit.is_translatable:
                    results.append(unit.content)
                    if path:
                        progress_manager.add_chunk_result(path, idx, unit.content)
                    continue
                # LLM 번역
                translated = self.translate_unit(unit.content, source_lang)
                results.append(translated)
                if path:
                    progress_manager.add_chunk_result(path, idx, translated)
            if path:
                progress_manager.finish(path)
        except Exception as e:
            if path:
                progress_manager.error(path, str(e))
            raise
        # 번역 결과를 원래 구조대로 조립
        return "\n".join(results)


def translate_pdf_to_korean(pdf_path: str, model_name: str = "gemma3:4b") -> str:
    """PDF 파일을 Markdown으로 변환 후 한국어로 번역"""
    md = pdf_to_markdown(pdf_path)
    config = TranslationConfig(model_name=model_name)
    translator = MultilingualTranslator(config)
    start = time.time()
    result = translator.translate_markdown(md, config.source_lang.value)
    duration = time.time() - start
    print(f"번역 완료: {duration:.1f}s")
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python ollama_translator.py <pdf 파일 경로> [모델명]")
        sys.exit(1)

    pdf_file = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "gemma3:4b"
    translated = translate_pdf_to_korean(pdf_file, model)
    output = Path(pdf_file).stem + "_korean.md"
    Path(output).write_text(translated, encoding="utf-8")
    print(f"결과 저장: {output}")
